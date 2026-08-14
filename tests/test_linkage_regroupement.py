"""Tests du regroupement transitif et de la métrique de grappe.

Exige la base pour la propriété du plateau haut (population réelle,
prédiction réelle, vérité terrain réelle) — placé dans le job qui en a
une. Aucun littéral de volumétrie : chaque grandeur comparée est mesurée
à l'exécution.
"""

from pathlib import Path

import yaml

from linkage.population import extraire_population
from linkage.regroupement import (
    composantes_connexes,
    metrique_grappe,
    partition_verite_terrain,
    regrouper,
    tailles_des_grappes,
)

RACINE = Path(__file__).resolve().parent.parent
VERITE_TERRAIN = RACINE / "generator" / "output" / "scenario_30" / "verite_terrain.yml"


def _population_synthetique(identifiants: list[str]) -> list[dict]:
    return [{"n_ipp": i} for i in identifiants]


def _partition_en_sets(affectation: dict[str, str]) -> set[frozenset]:
    groupes: dict[str, set[str]] = {}
    for n_ipp, cluster_id in affectation.items():
        groupes.setdefault(cluster_id, set()).add(n_ipp)
    return {frozenset(membres) for membres in groupes.values()}


def test_graphe_construit_a_la_main_donne_la_partition_attendue():
    # Trois enregistrements en chaîne transitive (A-B et B-C, mais pas A-C
    # directement) doivent former UNE seule grappe {A, B, C} ; D et E
    # forment une deuxième composante disjointe {D, E} ; F reste seul.
    identifiants = ["A", "B", "C", "D", "E", "F"]
    population = _population_synthetique(identifiants)
    paires = [
        ("A", "B", 0.9),
        ("B", "C", 0.9),
        ("D", "E", 0.9),
    ]

    affectation = composantes_connexes(paires, seuil=0.5, population=population)
    partition_obtenue = _partition_en_sets(affectation)
    partition_attendue = {frozenset({"A", "B", "C"}), frozenset({"D", "E"}), frozenset({"F"})}

    assert partition_obtenue == partition_attendue


def test_somme_des_tailles_egale_nombre_d_enregistrements():
    identifiants = ["A", "B", "C", "D", "E", "F"]
    population = _population_synthetique(identifiants)
    paires = [("A", "B", 0.9), ("B", "C", 0.9), ("D", "E", 0.9)]

    affectation = composantes_connexes(paires, seuil=0.5, population=population)
    tailles = tailles_des_grappes(affectation)

    assert sum(tailles.values()) == len(identifiants)


def test_plateau_haut_egale_le_nombre_de_paires_verite_terrain_presentes():
    population = extraire_population()
    n_ipp_valides = {enregistrement["n_ipp"] for enregistrement in population}

    with VERITE_TERRAIN.open(encoding="utf-8") as f:
        verite_terrain = yaml.safe_load(f)
    paires = verite_terrain["doublons"]["paires"]
    paires_presentes = [
        (p["n_ipp_1"], p["n_ipp_2"])
        for p in paires
        if p["n_ipp_1"] in n_ipp_valides and p["n_ipp_2"] in n_ipp_valides
    ]
    assert paires_presentes, "aucune paire de vérité terrain présente : rien à mesurer"

    # Un seuil du plateau haut : au-dessus du maximum mesuré des paires non
    # vraies, en dessous du minimum des paires vraies.
    affectation = regrouper(0.5, population)
    tailles = tailles_des_grappes(affectation)
    nb_grappes_taille_deux = sum(1 for taille in tailles.values() if taille == 2)

    assert nb_grappes_taille_deux == len(paires_presentes)


def test_grappe_predite_sur_fusionnee_ne_compte_pas_comme_retrouvee():
    """La reconnaissance d'une grappe vraie exige une ÉGALITÉ exacte, pas
    une inclusion : une grappe vraie {A, B} contenue dans une grappe
    prédite plus grande {A, B, C} (sur-fusion) ne doit PAS compter comme
    retrouvée. Sans ce test, une confusion inclusion/égalité resterait
    invisible : le contrôle positif (la partition vraie contre elle-même)
    ne peut pas la détecter, une grappe étant toujours son propre sous-
    ensemble.
    """
    partition_vraie = {"A": "vt_0", "B": "vt_0", "C": "C"}
    partition_predite_sur_fusionnee = {"A": "p", "B": "p", "C": "p"}

    resultat = metrique_grappe(partition_predite_sur_fusionnee, partition_vraie)

    assert resultat["vraies_retrouvees"] == 0
    assert resultat["enregistrements_sur_fusionnes"] == 3


def test_metrique_sur_la_verite_terrain_contre_elle_meme_est_parfaite():
    population = extraire_population()
    n_ipp_valides = {enregistrement["n_ipp"] for enregistrement in population}

    with VERITE_TERRAIN.open(encoding="utf-8") as f:
        verite_terrain = yaml.safe_load(f)
    paires = verite_terrain["doublons"]["paires"]
    paires_presentes = [
        (p["n_ipp_1"], p["n_ipp_2"])
        for p in paires
        if p["n_ipp_1"] in n_ipp_valides and p["n_ipp_2"] in n_ipp_valides
    ]

    partition_vraie = partition_verite_terrain(population, paires_presentes)
    resultat = metrique_grappe(partition_vraie, partition_vraie)

    assert resultat["predites_sans_correspondance"] == 0
    assert resultat["enregistrements_sur_fusionnes"] == 0
    assert resultat["vraies_retrouvees"] == len(set(partition_vraie.values()))
