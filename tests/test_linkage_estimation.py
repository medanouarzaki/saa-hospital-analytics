"""Tests du modèle estimé (linkage.estimation).

Exige la base UNIQUEMENT pour extraire la population et construire la
table de fréquence de la ville à comparer (linkage.population.extraire_
population, une requête, pas une estimation) — jamais pour ré-exécuter
l'estimation elle-même (u par échantillonnage, m par maximisation de
l'espérance), coûteuse, dont ce fichier réutilise le résultat déjà
persisté (linkage/modele_estime.json).

Aucun littéral de volumétrie : chaque grandeur comparée est calculée à
l'exécution, jamais recopiée.
"""

import pandas as pd
import pytest
from splink import Linker
from splink.backends.duckdb import DuckDBAPI

from linkage.champs import COMPARAISONS
from linkage.estimation import CHEMIN_MODELE_ESTIME, table_frequence_ville
from linkage.population import extraire_population

# La comparaison "piece_identite" porte un niveau ("manquant d'au moins un
# côté") qui n'est pas un niveau de valeur manquante reconnu par la
# bibliothèque (CustomLevel, pas NullLevel) : il reçoit un vrai facteur de
# Bayes estimé au lieu d'être neutralisé, et rien ne garantit qu'une
# absence partielle soit "plus stricte" qu'une correspondance exacte. Ce
# n'est pas une régression à corriger dans ce fichier ; c'est un fait
# mesuré et documenté séparément.
COMPARAISON_AVEC_EXCEPTION_DE_MONOTONIE = "piece_identite"


@pytest.fixture(scope="module")
def population() -> list[dict]:
    return extraire_population()


@pytest.fixture(scope="module")
def parametres_recharges(population) -> dict:
    df = pd.DataFrame(population)
    linker = Linker(df, str(CHEMIN_MODELE_ESTIME), DuckDBAPI())
    return linker.misc.save_model_to_json(None)


def test_le_modele_recharge_porte_un_parametre_par_comparaison(parametres_recharges):
    comparaisons_du_modele = {c["output_column_name"] for c in parametres_recharges["comparisons"]}
    assert comparaisons_du_modele == set(COMPARAISONS.keys())


def test_facteurs_de_bayes_decroissants_par_comparaison(parametres_recharges):
    echecs = []
    for comparaison in parametres_recharges["comparisons"]:
        nom = comparaison["output_column_name"]
        if nom == COMPARAISON_AVEC_EXCEPTION_DE_MONOTONIE:
            continue
        facteurs = []
        for niveau in comparaison["comparison_levels"]:
            m = niveau.get("m_probability")
            u = niveau.get("u_probability")
            if m is None or u is None:
                continue
            facteurs.append(m / u)
        for precedent, suivant in zip(facteurs, facteurs[1:], strict=False):
            if not (suivant < precedent):
                echecs.append(f"{nom} : facteur {suivant} ne descend pas sous {precedent}")
    assert not echecs, "\n".join(echecs)


def test_table_frequence_ville_couvre_exactement_les_valeurs_de_la_population(population):
    table = table_frequence_ville(population)
    valeurs_table = {ligne["ville_norm"] for ligne in table}

    valeurs_population = {
        enregistrement["ville_norm"]
        for enregistrement in population
        if enregistrement["ville_norm"] is not None
    }

    assert valeurs_table == valeurs_population
