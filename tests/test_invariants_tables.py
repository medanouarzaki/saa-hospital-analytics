"""Contrôles génériques applicables à toute table du registre de l'orchestrateur.

Ce fichier ne cite aucun nom de table ni de colonne en dur : il parcourt
`generator.execution.REGISTRE_GENERATEURS` et applique, à chaque table qui y figure, les
sept mêmes contrôles. Une table ajoutée à ce registre est couverte sans qu'une ligne de ce
fichier change ; une table qui n'y figure pas n'est pas couverte, ce qui est le sens même
de « toute table produite ».

La génération complète (les trois tables actuellement couvertes) prend plusieurs dizaines
de secondes ; elle est partagée entre les sept contrôles par une fixture de portée module
plutôt que refaite à chaque test.
"""

import csv
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

from generator import config, ecriture, execution, nomenclatures, registre

RACINE = Path(__file__).resolve().parent.parent
GRAINE = 1

# part de valeurs à minuit tolérée sur une colonne d'horodatage réellement tirée dans un
# profil horaire : seuil déjà établi (generator/config/temporel.yml, profil "programme",
# poids nul aux heures 0-7) et repris tel quel, très au-dessus de zéro pour ne pas être
# fragile, très en-deçà d'un horodatage trivial (100 % à minuit, défaut historique corrigé
# avant l'écriture de ce fichier).
SEUIL_PART_MINUIT = 0.01


def entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


@pytest.fixture(scope="module")
def generation(tmp_path_factory) -> dict:
    entrees = entrees_config()
    racine = tmp_path_factory.mktemp("invariants_generation")
    execution_obj, lignes = execution.executer(racine, GRAINE, entrees=entrees)
    return {"entrees": entrees, "execution": execution_obj, "lignes": lignes}


def _lire_entete(execution_obj: ecriture.Execution, table: str) -> list[str]:
    partitions = sorted(p for p in execution_obj.partitions[table] if p.endswith(".csv"))
    assert partitions, f"{table} : aucune partition écrite"
    chemin = execution_obj.racine / partitions[0]
    with chemin.open(encoding="utf-8") as f:
        return next(csv.reader(f))


def test_entetes_exactement_les_colonnes_du_registre(generation: dict) -> None:
    execution_obj: ecriture.Execution = generation["execution"]

    for table in execution.tables_couvertes():
        colonnes_attendues = registre.colonnes_table(table)
        entete = _lire_entete(execution_obj, table)
        assert entete == colonnes_attendues, table


def test_conformite_nomenclatures_toutes_colonnes_codees(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    correspondance = entrees["correspondance_colonnes_nomenclatures"]["valeur"]

    for table in execution.tables_couvertes():
        lignes_table = lignes[table]
        colonnes_codees = [c for c in correspondance if c["table"] == table]

        for correspondance_colonne in colonnes_codees:
            colonne = correspondance_colonne["colonne"]
            nom_nomenclature = nomenclatures.nomenclature_colonne(table, colonne, entrees)
            codes_valides = set(nomenclatures.codes_nomenclature(nom_nomenclature, entrees))

            valeurs_observees = {
                ligne[colonne] for ligne in lignes_table if ligne[colonne] is not None
            }
            hors_nomenclature = valeurs_observees - codes_valides
            assert not hors_nomenclature, (table, colonne, nom_nomenclature, hors_nomenclature)


def test_bornage_partitions(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    n_jours_periode = (date_fin - date_debut).days + 1

    for table in execution.tables_couvertes():
        lignes_table = lignes[table]
        dates_extraction = {ligne["date_extraction"] for ligne in lignes_table}
        assert dates_extraction, table
        hors_periode = {d for d in dates_extraction if d < date_debut or d > date_fin}
        assert not hors_periode, (table, sorted(hors_periode))
        assert len(dates_extraction) <= n_jours_periode, (table, len(dates_extraction))


def test_horodatages_non_triviaux(generation: dict) -> None:
    lignes = generation["lignes"]

    with (RACINE / "docs" / "champs" / "registre_champs.yml").open(encoding="utf-8") as f:
        registre_brut = yaml.safe_load(f)
    colonnes_horodatage = [
        (e["table"], e["colonne"]) for e in registre_brut if e["type_metier"] == "horodatage"
    ]

    for table in execution.tables_couvertes():
        lignes_table = lignes[table]
        for tbl, colonne in colonnes_horodatage:
            if tbl != table:
                continue
            valeurs: list[datetime] = [
                ligne[colonne] for ligne in lignes_table if ligne.get(colonne) is not None
            ]
            if not valeurs:
                continue
            n_minuit = sum(1 for v in valeurs if v.hour == 0 and v.minute == 0 and v.second == 0)
            part_minuit = n_minuit / len(valeurs)
            assert part_minuit < SEUIL_PART_MINUIT, (table, colonne, part_minuit)


def test_aucune_colonne_degeneree(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    identifiants_par_table: dict[str, set[str]] = {}
    for c in entrees["colonnes_identifiants"]["valeur"]:
        identifiants_par_table.setdefault(c["table"], set()).add(c["colonne"])

    exceptions_par_table: dict[str, set[str]] = {}
    for c in entrees["colonnes_degenerees_declarees"]["valeur"]:
        exceptions_par_table.setdefault(c["table"], set()).add(c["colonne"])

    for table in execution.tables_couvertes():
        lignes_table = lignes[table]
        n = len(lignes_table)
        identifiants = identifiants_par_table.get(table, set())
        exceptions = exceptions_par_table.get(table, set())

        for colonne in registre.colonnes_table(table):
            if colonne in identifiants or colonne in exceptions:
                continue
            valeurs = {ligne[colonne] for ligne in lignes_table}
            assert len(valeurs) != 1, (table, colonne, "une seule valeur distincte")
            assert len(valeurs) != n, (
                table,
                colonne,
                f"autant de valeurs distinctes que de lignes ({n})",
            )


def test_coherence_intra_ligne(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    correspondance_contraintes = entrees["contraintes_coherence_par_table"]["valeur"]

    for table in execution.tables_couvertes():
        nom_parametre = correspondance_contraintes.get(table)
        if nom_parametre is None:
            continue
        lignes_table = lignes[table]
        total = len(lignes_table)

        for contrainte in entrees[nom_parametre]["valeur"]:
            tolerance = contrainte["tolerance"]
            nature = contrainte["nature"]
            colonne_a = contrainte["colonne_a"]
            colonne_b = contrainte["colonne_b"]

            if nature == "egalite":
                n_violations = sum(
                    1 for ligne in lignes_table if ligne[colonne_a] != ligne[colonne_b]
                )
            elif nature == "appartenance":
                n_violations = sum(
                    1
                    for ligne in lignes_table
                    if ligne[colonne_a] == contrainte["valeur_a_declenchante"]
                    and ligne[colonne_b] in contrainte["valeurs_b_interdites"]
                )
            elif nature == "derivation":
                table_derivation = entrees[contrainte["table_derivation"]]["valeur"]
                n_violations = sum(
                    1
                    for ligne in lignes_table
                    if ligne[colonne_b] != table_derivation.get(ligne[colonne_a])
                )
            elif nature == "presence_conditionnee":
                declenchante = contrainte["valeur_a_declenchante"]
                n_violations = sum(
                    1
                    for ligne in lignes_table
                    if (ligne[colonne_a] == declenchante) != (ligne[colonne_b] is not None)
                )
            else:
                raise ValueError(f"nature de contrainte inconnue : {nature!r}")

            part_violations = n_violations / total
            assert part_violations <= tolerance, (
                table,
                colonne_a,
                colonne_b,
                nature,
                part_violations,
            )


def test_reproductibilite_deux_graines_deux_formats(generation: dict) -> None:
    entrees = generation["entrees"]

    def executer(graine: int, racine: Path) -> ecriture.Execution:
        execution_obj, _ = execution.executer(racine, graine, entrees=entrees)
        return execution_obj

    racine_a1 = generation["execution"].racine.parent / "repro_invariants_a1"
    racine_a2 = generation["execution"].racine.parent / "repro_invariants_a2"
    racine_b = generation["execution"].racine.parent / "repro_invariants_b"

    execution_a1 = executer(GRAINE, racine_a1)
    execution_a2 = executer(GRAINE, racine_a2)
    execution_b = executer(GRAINE + 1, racine_b)

    for suffixe in (".csv", ".parquet"):
        empreintes_a1 = {k: v for k, v in execution_a1.empreintes.items() if k.endswith(suffixe)}
        empreintes_a2 = {k: v for k, v in execution_a2.empreintes.items() if k.endswith(suffixe)}
        assert empreintes_a1 == empreintes_a2, suffixe

        empreintes_b = {k: v for k, v in execution_b.empreintes.items() if k.endswith(suffixe)}
        # contrôle positif : une graine différente doit produire des empreintes différentes
        assert empreintes_a1 != empreintes_b, suffixe
