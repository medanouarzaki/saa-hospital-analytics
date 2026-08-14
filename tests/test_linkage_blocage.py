"""Tests des règles de blocage (linkage.blocage).

Exige une base PostgreSQL chargée avec marts.dim_patient déjà matérialisée
(voir tests/test_linkage_population.py). Aucun littéral de volumétrie :
chaque grandeur comparée est mesurée à l'exécution, jamais recopiée.
"""

import os
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import yaml
from splink.backends.duckdb import DuckDBAPI
from splink.blocking_analysis import (
    cumulative_comparisons_to_be_scored_from_blocking_rules_data,
)

from linkage.blocage import colonne_blocage, regles_blocage
from linkage.population import extraire_population

RACINE = Path(__file__).resolve().parent.parent
VERITE_TERRAIN_DEFAUT = RACINE / "generator" / "output" / "scenario_30" / "verite_terrain.yml"
# Même convention que tests/test_dim_patient.py (VERITE_TERRAIN_PATIENTS) : le
# générateur écrit sous la racine passée en argument, pas nécessairement
# generator/output/ (le job dbt de la CI génère sous $RUNNER_TEMP/scenario/) — un
# chemin en dur lirait la vérité terrain d'une autre exécution, ou aucune sur un
# clone neuf.
VERITE_TERRAIN = Path(os.environ.get("VERITE_TERRAIN_PATIENTS", str(VERITE_TERRAIN_DEFAUT)))

_NOMS_CHAMPS_PAR_REGLE = [
    ("type_piece_identite", "n_piece_identite"),
    ("nom_famille_1", "telephone_1"),
    ("nom_famille_1", "adresse"),
    ("nom_pere", "nom_mere", "date_naissance"),
]


@pytest.fixture(scope="module")
def population() -> list[dict]:
    return extraire_population()


@pytest.fixture(scope="module")
def dataframe(population) -> pd.DataFrame:
    return pd.DataFrame(population)


@pytest.fixture(scope="module")
def connexion_duckdb(dataframe):
    con = duckdb.connect(":memory:")
    con.register("pop", dataframe)
    yield con
    con.close()


def _condition_union_sql() -> str:
    conditions = []
    for champs in _NOMS_CHAMPS_PAR_REGLE:
        colonnes = [colonne_blocage(c) for c in champs]
        cond = " and ".join(
            f"a.{c} = b.{c} and a.{c} is not null and b.{c} is not null" for c in colonnes
        )
        conditions.append(f"({cond})")
    return " or ".join(conditions)


def test_taille_union_bibliotheque_egale_taille_union_sql(dataframe, connexion_duckdb):
    db_api = DuckDBAPI()
    resultat = cumulative_comparisons_to_be_scored_from_blocking_rules_data(
        table_or_tables=[dataframe],
        blocking_rules=regles_blocage(),
        link_type="dedupe_only",
        db_api=db_api,
        unique_id_column_name="n_ipp",
    )
    taille_union_bibliotheque = int(resultat["cumulative_rows"].iloc[-1])

    condition_union = _condition_union_sql()
    (taille_union_sql,) = connexion_duckdb.execute(
        f"select count(*) from pop a join pop b on a.n_ipp < b.n_ipp where {condition_union}"
    ).fetchone()

    assert taille_union_bibliotheque == taille_union_sql


def test_rappel_union_egale_nb_paires_verite_terrain_presentes(population, connexion_duckdb):
    n_ipp_valides = {enregistrement["n_ipp"] for enregistrement in population}

    with VERITE_TERRAIN.open(encoding="utf-8") as f:
        verite_terrain = yaml.safe_load(f)
    paires = verite_terrain["doublons"]["paires"]

    paires_presentes = [
        p for p in paires if p["n_ipp_1"] in n_ipp_valides and p["n_ipp_2"] in n_ipp_valides
    ]
    assert paires_presentes, "aucune paire de vérité terrain présente : rien à mesurer"

    condition_union = _condition_union_sql()
    nb_captees = 0
    for paire in paires_presentes:
        n1, n2 = sorted([paire["n_ipp_1"], paire["n_ipp_2"]])
        (trouvee,) = connexion_duckdb.execute(
            f"select count(*) from pop a join pop b "
            f"on a.n_ipp = ? and b.n_ipp = ? where {condition_union}",
            [n1, n2],
        ).fetchone()
        if trouvee:
            nb_captees += 1

    assert nb_captees == len(paires_presentes), (
        f"{nb_captees} paires captées sur {len(paires_presentes)} présentes"
    )
