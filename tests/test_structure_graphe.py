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

_MOTIF_ABOUTISSEMENT_VIDE = re.compile(r'^echo "[^"\n]*"\n$')
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


def test_taches_terminales_aboutissement_vide() -> None:
    """Critère explicite, pas une inspection approximative : la commande de chaque tâche
    terminale ne contient rien d'autre qu'un unique `echo` sur une seule ligne."""
    dag = _charger_dag()
    for task_id in ("exporter", "rafraichir_instantane"):
        tache = dag.get_task(task_id)
        assert _MOTIF_ABOUTISSEMENT_VIDE.match(tache.bash_command), (
            f"{task_id} : commande non reconnue comme un aboutissement vide : "
            f"{tache.bash_command!r}"
        )


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
