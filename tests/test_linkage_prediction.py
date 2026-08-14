"""Tests de la prédiction et du peuplement de linkage.paires_candidates.

Exige une base déjà peuplée par `linkage.prediction` (lecture seule : ne
relance jamais la prédiction, coûteuse, ce fichier lit la table déjà
écrite). Aucun littéral, y compris de volumétrie : chaque grandeur
comparée est mesurée à l'exécution.
"""

import os
from pathlib import Path

import pandas as pd
import pytest
import yaml
from splink.backends.duckdb import DuckDBAPI
from splink.blocking_analysis import (
    cumulative_comparisons_to_be_scored_from_blocking_rules_data,
)

from linkage.blocage import regles_blocage
from linkage.champs import COMPARAISONS
from linkage.population import _connexion, extraire_population

RACINE = Path(__file__).resolve().parent.parent
VERITE_TERRAIN_DEFAUT = RACINE / "generator" / "output" / "scenario_30" / "verite_terrain.yml"
# Même convention que tests/test_dim_patient.py (VERITE_TERRAIN_PATIENTS) : voir
# tests/test_linkage_blocage.py pour la justification complète.
VERITE_TERRAIN = Path(os.environ.get("VERITE_TERRAIN_PATIENTS", str(VERITE_TERRAIN_DEFAUT)))


@pytest.fixture(scope="module")
def population() -> list[dict]:
    return extraire_population()


@pytest.fixture(scope="module")
def connexion():
    with _connexion() as cnx:
        yield cnx


def test_taille_table_egale_taille_union_blocage(connexion, population):
    with connexion.cursor() as curseur:
        curseur.execute("select count(*) from linkage.paires_candidates")
        (taille_table,) = curseur.fetchone()

    db_api = DuckDBAPI()
    dataframe = pd.DataFrame(population)
    resultat = cumulative_comparisons_to_be_scored_from_blocking_rules_data(
        table_or_tables=[dataframe],
        blocking_rules=regles_blocage(),
        link_type="dedupe_only",
        db_api=db_api,
        unique_id_column_name="n_ipp",
    )
    taille_union = int(resultat["cumulative_rows"].iloc[-1])

    assert taille_table == taille_union


def test_aucune_ligne_ne_viole_l_ordre_canonique(connexion):
    with connexion.cursor() as curseur:
        curseur.execute(
            "select count(*) from linkage.paires_candidates where not (n_ipp_1 < n_ipp_2)"
        )
        (nb_violations,) = curseur.fetchone()
    assert nb_violations == 0


def test_rappel_du_blocage_est_total_sur_la_verite_terrain(connexion, population):
    n_ipp_valides = {enregistrement["n_ipp"] for enregistrement in population}
    with VERITE_TERRAIN.open(encoding="utf-8") as f:
        verite_terrain = yaml.safe_load(f)
    paires = verite_terrain["doublons"]["paires"]

    paires_presentes = [
        tuple(sorted([p["n_ipp_1"], p["n_ipp_2"]]))
        for p in paires
        if p["n_ipp_1"] in n_ipp_valides and p["n_ipp_2"] in n_ipp_valides
    ]
    assert paires_presentes, "aucune paire de vérité terrain présente : rien à mesurer"

    with connexion.cursor() as curseur:
        curseur.execute(
            f"select count(*) from linkage.paires_candidates where (n_ipp_1, n_ipp_2) in "
            f"({','.join(['(%s,%s)'] * len(paires_presentes))})",
            [valeur for paire in paires_presentes for valeur in paire],
        )
        (nb_trouvees,) = curseur.fetchone()

    assert nb_trouvees == len(paires_presentes)


def test_probabilite_entre_zero_et_un(connexion):
    with connexion.cursor() as curseur:
        curseur.execute(
            "select count(*) from linkage.paires_candidates "
            "where probabilite < 0 or probabilite > 1"
        )
        (nb_hors_bornes,) = curseur.fetchone()
    assert nb_hors_bornes == 0


def test_chaque_colonne_de_niveau_porte_au_moins_deux_valeurs_distinctes(connexion):
    echecs = []
    with connexion.cursor() as curseur:
        for nom in COMPARAISONS:
            curseur.execute(f"select count(distinct niveau_{nom}) from linkage.paires_candidates")
            (nb_distinctes,) = curseur.fetchone()
            if nb_distinctes < 2:
                echecs.append(f"niveau_{nom} : {nb_distinctes} valeur(s) distincte(s)")
    assert not echecs, "\n".join(echecs)
