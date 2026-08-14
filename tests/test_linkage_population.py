"""Tests de l'extraction de la population de rapprochement (linkage.population).

Exige une base PostgreSQL chargée avec marts.dim_patient déjà matérialisée par dbt (les
modèles doivent avoir tourné). Les paramètres de connexion viennent de l'environnement du
processus ; POSTGRES_HOST est obligatoire (voir linkage.population.parametres_connexion),
les autres ont des valeurs par défaut non secrètes. Aucun skip silencieux : une base absente
ou non chargée fait échouer le test, pas le sauter.
"""

import pytest

from linkage.champs import CHAMPS_COMPARES, COLONNES_ECARTEES, Normalisation
from linkage.normalisation import v1, v2
from linkage.population import _connexion, extraire_population


@pytest.fixture(scope="module")
def population():
    return extraire_population()


@pytest.fixture(scope="module")
def decompte_base() -> tuple[int, int]:
    """(n_ipp distincts, lignes) mesurés directement en base, indépendamment de
    l'extraction, pour comparaison."""
    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "SELECT count(DISTINCT n_ipp), count(*) FROM marts.dim_patient WHERE est_courante"
        )
        distinct_n_ipp, total_lignes = curseur.fetchone()
    return distinct_n_ipp, total_lignes


def test_une_ligne_par_n_ipp(population, decompte_base):
    distinct_n_ipp_base, total_lignes_base = decompte_base
    n_ipp_extraits = [enregistrement["n_ipp"] for enregistrement in population]

    assert len(population) == len(set(n_ipp_extraits)), "n_ipp dupliqués dans l'extraction"
    assert len(population) == distinct_n_ipp_base
    assert distinct_n_ipp_base == total_lignes_base, (
        "la base elle-même a des n_ipp dupliqués en version courante"
    )


def test_toutes_les_colonnes_du_registre_sont_presentes(population):
    assert len(population) > 0, "population vide : rien à vérifier"
    premiere_ligne = population[0]
    for nom_champ in CHAMPS_COMPARES:
        assert nom_champ in premiere_ligne, f"colonne brute manquante : {nom_champ}"


def test_aucune_colonne_ecartee_ne_figure_dans_le_resultat(population):
    assert len(population) > 0
    premiere_ligne = population[0]
    for nom_ecartee in COLONNES_ECARTEES:
        assert nom_ecartee not in premiere_ligne, f"colonne écartée présente : {nom_ecartee}"


def test_colonnes_normalisees_sont_effectivement_normalisees(population):
    assert len(population) > 0
    fonctions = {Normalisation.V1: v1, Normalisation.V2: v2}
    for nom_champ, champ in CHAMPS_COMPARES.items():
        if champ.normalisation is Normalisation.AUCUNE:
            continue
        fonction = fonctions[champ.normalisation]
        colonne_norm = f"{nom_champ}_norm"
        for enregistrement in population:
            assert colonne_norm in enregistrement, f"colonne normalisée absente : {colonne_norm}"
            valeur_normalisee = enregistrement[colonne_norm]
            # réappliquer la normalisation à une valeur déjà normalisée ne la change pas
            assert fonction(valeur_normalisee) == valeur_normalisee, (
                f"{colonne_norm} n'est pas stable sous {champ.normalisation}"
            )


def test_date_naissance_sans_normalisation_textuelle(population):
    assert CHAMPS_COMPARES["date_naissance"].normalisation is Normalisation.AUCUNE
    assert len(population) > 0
    for enregistrement in population:
        # le registre déclare date_naissance sans normalisation : ou bien aucune colonne
        # normalisée n'existe, ou bien elle est égale à la colonne brute.
        if "date_naissance_norm" in enregistrement:
            assert enregistrement["date_naissance_norm"] == enregistrement["date_naissance"]
        else:
            assert "date_naissance_norm" not in enregistrement
