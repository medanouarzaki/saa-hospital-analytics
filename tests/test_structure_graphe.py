"""Structure du graphe quotidien, chargé par la classe de chargement de l'orchestrateur — pas
par la ligne de commande, pas de base ni d'orchestrateur en service requis. Toutes les propriétés
sont exprimées en relations entre tâches (`upstream_task_ids`/`downstream_task_ids`), jamais en
rang numérique dans une liste.
"""

import ast
import re
import sys
from pathlib import Path

import pytest
from airflow.dag_processing.dagbag import DagBag

RACINE = Path(__file__).resolve().parent.parent
FICHIER_GRAPHE = RACINE / "airflow" / "saa_daily.py"

MODULES_PROJET = {"ingestion", "linkage", "generator", "dashboard", "dbt"}

# Les modules que les deux tâches terminales doivent invoquer. La correspondance est portée ici et
# nulle part ailleurs : c'est elle que le contrôle confronte à ce que le graphe déclare.
MODULES_TERMINAUX = {
    "rafraichir_instantane": "instantane.rafraichir",
    "exporter": "livraison.exporter",
}
_MOTIF_CREDENTIAL_LITTERAL = re.compile(r'(?i)(password|secret|token)\s*[:=]\s*["\'][^"\']{4,}')


def _charger_dag():
    dagbag = DagBag(dag_folder=str(FICHIER_GRAPHE.parent))
    assert not dagbag.import_errors, f"erreurs d'import : {dagbag.import_errors}"
    return dagbag.dags["saa_daily"]


def test_controle_qualite_suit_le_chargement_et_precede_dbt() -> None:
    dag = _charger_dag()
    controle = dag.get_task("controle_qualite")
    assert controle.upstream_task_ids == {"charger_journee"}
    assert controle.downstream_task_ids == {"dbt_intermediaire"}


def test_dimensions_avant_faits() -> None:
    dag = _charger_dag()
    dimensions = dag.get_task("dbt_dimensions")
    faits = dag.get_task("dbt_faits")
    assert faits.task_id in dimensions.downstream_task_ids
    assert dimensions.task_id in faits.upstream_task_ids


def test_rapprochement_apres_faits_et_avant_agregats() -> None:
    dag = _charger_dag()
    faits = dag.get_task("dbt_faits")
    tests = dag.get_task("dbt_tests")
    prediction = dag.get_task("rapprochement_prediction")
    evaluation = dag.get_task("rapprochement_regroupement_evaluation")
    agregats = dag.get_task("dbt_agregats")

    assert tests.task_id in faits.downstream_task_ids
    assert prediction.task_id in tests.downstream_task_ids
    assert evaluation.task_id in prediction.downstream_task_ids
    assert agregats.task_id in evaluation.downstream_task_ids


def test_taches_terminales_invoquent_leur_module() -> None:
    """Chaque tâche terminale invoque bien le module attendu.

    Cette propriété a remplacé son inverse : les deux tâches étaient des aboutissements vides, et
    un contrôle vérifiait qu'elles ne faisaient rien. Elles font désormais quelque chose, et c'est
    ce quelque chose qui est vérifié — nommément, non par une inspection approximative.
    """
    dag = _charger_dag()
    fautifs = []
    for task_id, module in MODULES_TERMINAUX.items():
        commande = dag.get_task(task_id).bash_command
        if f"-m {module}" not in commande:
            fautifs.append(f"{task_id} : n'invoque pas {module} — {commande.strip()!r}")
    assert not fautifs, "tâches terminales mal branchées : " + " | ".join(fautifs)


def test_taches_terminales_ont_un_repertoire_de_travail() -> None:
    """Sans répertoire de travail, l'opérateur exécute dans un répertoire temporaire propre à
    l'appel, jamais le dépôt — la commande échouerait sans que le graphe soit en cause.

    Le répertoire attendu est celui que les autres tâches du dépôt emploient déjà : le contrôle le
    relève sur elles plutôt que de l'écrire, de sorte qu'un changement de convention ne le laisse
    pas vérifier une valeur périmée.
    """
    dag = _charger_dag()
    references = {
        tache.cwd for tache in dag.tasks if tache.task_id not in MODULES_TERMINAUX and tache.cwd
    }
    assert references, "aucune tâche de référence ne porte de répertoire de travail"

    fautifs = []
    for task_id in MODULES_TERMINAUX:
        cwd = dag.get_task(task_id).cwd
        if not cwd:
            fautifs.append(f"{task_id} : aucun répertoire de travail")
        elif cwd not in references:
            fautifs.append(f"{task_id} : répertoire {cwd!r} hors de ceux des autres tâches")
    assert not fautifs, "répertoires de travail manquants ou inattendus : " + " | ".join(fautifs)


def test_le_rafraichissement_precede_l_export() -> None:
    """L'export lit l'instantané : le lire avant qu'il ne soit constitué livrerait l'état de la
    veille, sans qu'aucune tâche n'échoue."""
    dag = _charger_dag()
    rafraichissement = dag.get_task("rafraichir_instantane")
    export = dag.get_task("exporter")
    assert export.task_id in rafraichissement.downstream_task_ids, (
        f"l'export n'est pas en aval du rafraîchissement : aval du rafraîchissement = "
        f"{sorted(rafraichissement.downstream_task_ids)}"
    )
    assert rafraichissement.task_id in export.upstream_task_ids


def test_les_taches_terminales_suivent_le_controle_de_qualite() -> None:
    """Un livrable produit malgré un contrôle de qualité bloqué serait pire qu'un livrable absent.

    La vérification porte sur l'amont TRANSITIF : une dépendance directe n'est pas exigée, seule
    compte l'impossibilité qu'une tâche terminale s'exécute sans que le contrôle ait réussi.
    """
    dag = _charger_dag()

    def amont_transitif(task_id: str, vus: set[str] | None = None) -> set[str]:
        vus = set() if vus is None else vus
        for amont in dag.get_task(task_id).upstream_task_ids:
            if amont not in vus:
                vus.add(amont)
                amont_transitif(amont, vus)
        return vus

    fautifs = [
        task_id
        for task_id in MODULES_TERMINAUX
        if "controle_qualite" not in amont_transitif(task_id)
    ]
    assert not fautifs, f"tâches terminales sans contrôle de qualité en amont : {fautifs}"


def test_aucun_import_de_module_du_projet() -> None:
    arbre = ast.parse(FICHIER_GRAPHE.read_text(encoding="utf-8"))
    modules_importes = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            modules_importes.update(alias.name.split(".")[0] for alias in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            modules_importes.add(noeud.module.split(".")[0])
    intersection = modules_importes & MODULES_PROJET
    assert not intersection, f"import de module du projet trouvé : {intersection}"


def test_aucun_identifiant_ni_mot_de_passe() -> None:
    contenu = FICHIER_GRAPHE.read_text(encoding="utf-8")
    trouve = _MOTIF_CREDENTIAL_LITTERAL.search(contenu)
    assert trouve is None, f"motif ressemblant à un identifiant : {trouve.group(0)!r}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
