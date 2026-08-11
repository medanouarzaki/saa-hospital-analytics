"""Contrôles propres à la table des mouvements (generator/mouvements.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement : la
bijection avec les passages d'hospitalisation, les journées et la durée moyenne de séjour
au regard des cibles mesurées, la capacité litière jamais dépassée, l'absence de
chevauchement de lit, l'ordre des horodatages, les séjours en cours et l'absence de toute
activité chirurgicale. Consomme la génération partagée de tests/conftest.py.
"""

import re
from collections import defaultdict
from datetime import date, datetime

import pytest
import yaml

from generator import mouvements as mvt_mod
from generator import nomenclatures

TABLE = "source.mouvements"


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def _charger_verite_terrain(execution) -> dict:
    chemin = execution.racine / execution.scenario / "verite_terrain.yml"
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _par_sejour(lignes: list[dict]) -> dict[str, list[dict]]:
    groupes: dict[str, list[dict]] = defaultdict(list)
    for ligne in lignes:
        groupes[ligne["n_sejour"]].append(ligne)
    return groupes


def _admission(lignes_du_sejour: list[dict]) -> dict:
    return next(ligne for ligne in lignes_du_sejour if ligne["date_heure_admission"] is not None)


def _sortie(lignes_du_sejour: list[dict]) -> datetime | None:
    for ligne in lignes_du_sejour:
        if ligne["date_heure_sortie"] is not None:
            return ligne["date_heure_sortie"]
    return None


def _fin_pour_calcul(lignes_du_sejour: list[dict], date_fin: date) -> datetime:
    sortie = _sortie(lignes_du_sejour)
    if sortie is not None:
        return sortie
    return datetime.combine(date_fin, datetime.max.time())


def _lignes_avec_lit_triees(lignes_du_sejour: list[dict]) -> list[dict]:
    avec_lit = [ligne for ligne in lignes_du_sejour if ligne["lit"] is not None]

    def cle(ligne: dict) -> datetime:
        return ligne["date_heure_admission"] or ligne["date_heure_mutation"]

    return sorted(avec_lit, key=cle)


def test_rattachement_bijection_avec_passages_hospitalisation(generation: dict) -> None:
    lignes_mvt = generation["lignes"][TABLE]
    lignes_passages = generation["lignes"]["source.passages"]
    lignes_h = [ligne for ligne in lignes_passages if ligne["type_passage"] == "H"]

    groupes = _par_sejour(lignes_mvt)
    assert len(groupes) == len(lignes_h)

    admissions_mouvements = set()
    for lignes_du_sejour in groupes.values():
        lignes_admission = [
            ligne for ligne in lignes_du_sejour if ligne["date_heure_admission"] is not None
        ]
        assert len(lignes_admission) == 1, "un séjour doit porter exactement une admission"
        admission = lignes_admission[0]
        admissions_mouvements.add((admission["n_ipp"], admission["date_heure_admission"]))

    admissions_passages = {(ligne["n_ipp"], ligne["date_heure_entree"]) for ligne in lignes_h}
    assert admissions_mouvements == admissions_passages


# les journees d'hospitalisation (par annee civile et sur la periode) et la duree moyenne
# de sejour sont verifiees par tests/test_coherence_inter_tables.py
# (conformite de volumetrie, et regle 13 pour la duree moyenne) -- deplacees depuis ce
# fichier plutot que dupliquees.


def test_capacite_jamais_depassee(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    capacite = entrees["capacite_litiere_fonctionnelle"]["valeur"]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    groupes = _par_sejour(lignes_mvt)
    evenements = []
    for lignes_du_sejour in groupes.values():
        lignes_triees = _lignes_avec_lit_triees(lignes_du_sejour)
        for indice, ligne in enumerate(lignes_triees):
            debut = ligne["date_heure_admission"] or ligne["date_heure_mutation"]
            if indice + 1 < len(lignes_triees):
                suivante = lignes_triees[indice + 1]
                fin = suivante["date_heure_admission"] or suivante["date_heure_mutation"]
            else:
                fin = _fin_pour_calcul(lignes_du_sejour, date_fin)
            evenements.append((debut, 1))
            evenements.append((fin, -1))

    # une depart (-1) au meme instant qu'une arrivee (+1) libere le lit avant qu'il ne
    # soit repris : traiter les departs en premier a timestamp egal, sinon un lit rendu et
    # aussitot repris compte deux occupants simultanes qui n'existent jamais reellement.
    evenements.sort(key=lambda e: (e[0], e[1]))
    occ = 0
    max_occ = 0
    for _, delta in evenements:
        occ += delta
        max_occ = max(max_occ, occ)

    assert max_occ <= capacite, (max_occ, capacite)


# le taux d'occupation moyen (TOM) est verifie par
# tests/test_coherence_inter_tables.py::test_regle_13..., deplace depuis ce fichier.


def test_lits_sans_collision(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    groupes = _par_sejour(lignes_mvt)
    intervalles_par_lit: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for lignes_du_sejour in groupes.values():
        lignes_triees = _lignes_avec_lit_triees(lignes_du_sejour)
        for indice, ligne in enumerate(lignes_triees):
            debut = ligne["date_heure_admission"] or ligne["date_heure_mutation"]
            if indice + 1 < len(lignes_triees):
                suivante = lignes_triees[indice + 1]
                fin = suivante["date_heure_admission"] or suivante["date_heure_mutation"]
            else:
                fin = _fin_pour_calcul(lignes_du_sejour, date_fin)
            intervalles_par_lit[ligne["lit"]].append((debut, fin))

    assert intervalles_par_lit, "aucun lit occupé à contrôler"
    for lit, intervalles in intervalles_par_lit.items():
        intervalles_tries = sorted(intervalles, key=lambda i: i[0])
        for (debut_a, fin_a), (debut_b, fin_b) in zip(
            intervalles_tries, intervalles_tries[1:], strict=False
        ):
            assert fin_a <= debut_b, (lit, (debut_a, fin_a), (debut_b, fin_b))


# l'ordre admission < mutation < sortie est verifie par
# tests/test_coherence_inter_tables.py::test_regle_06_aucune_sortie_anterieure_a_son_admission
# et test_regle_08_aucune_mutation_hors_intervalle_admission_sortie (regles inter-tables du
# cadrage, deplacees depuis ce fichier).


def test_sejours_en_cours(generation: dict) -> None:
    lignes_mvt = generation["lignes"][TABLE]
    lignes_passages = generation["lignes"]["source.passages"]
    lignes_h = [ligne for ligne in lignes_passages if ligne["type_passage"] == "H"]

    n_passages_sans_sortie = sum(1 for ligne in lignes_h if ligne["date_heure_sortie"] is None)

    groupes = _par_sejour(lignes_mvt)
    n_sejours_sans_sortie = sum(
        1 for lignes_du_sejour in groupes.values() if _sortie(lignes_du_sejour) is None
    )

    assert n_sejours_sans_sortie == n_passages_sans_sortie
    assert n_sejours_sans_sortie > 0


def test_mutation_change_toujours_unite(generation: dict) -> None:
    lignes_mvt = generation["lignes"][TABLE]

    mutations = [ligne for ligne in lignes_mvt if ligne["date_heure_mutation"] is not None]
    assert mutations, "aucune ligne de mutation à contrôler"
    for ligne in mutations:
        assert ligne["service_origine"] != ligne["service_destination"], ligne


def test_eligibilite_unites_maternite_pediatrie(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    lignes_pat = generation["lignes"]["source.patients"]

    age_max_pediatrie = entrees["age_maximal_revolus_pediatrie"]["valeur"]
    patients_par_ipp = {p["n_ipp"]: p for p in lignes_pat}

    vt = _charger_verite_terrain(generation["execution"])
    n_ipp_ages_exemptes = {entree["identifiant"] for entree in vt["ages_incoherents"]["entrees"]}
    assert len(n_ipp_ages_exemptes) == vt["ages_incoherents"]["decompte"]

    admissions = [ligne for ligne in lignes_mvt if ligne["date_heure_admission"] is not None]
    n_hgo = n_hped = 0
    for ligne in admissions:
        patient = patients_par_ipp[ligne["n_ipp"]]
        service = ligne["service_accueil"]
        if service == "HGO":
            n_hgo += 1
            assert patient["sexe"] == "F", ligne
        elif service == "HPED":
            if ligne["n_ipp"] in n_ipp_ages_exemptes:
                continue
            n_hped += 1
            age = mvt_mod._age_revolus(
                patient["date_naissance"], ligne["date_heure_admission"].date()
            )
            assert age <= age_max_pediatrie, (ligne, age)

    assert n_hgo > 0, "aucune admission HGO à contrôler"
    assert n_hped > 0, "aucune admission HPED à contrôler"


def test_somme_dotations_egale_capacite_totale(generation: dict) -> None:
    entrees = generation["entrees"]
    capacite_par_unite = entrees["capacite_par_unite"]["valeur"]
    capacite_totale = entrees["capacite_litiere_fonctionnelle"]["valeur"]

    assert sum(capacite_par_unite.values()) == capacite_totale


def test_occupation_maximale_par_unite_sous_dotation(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    capacite_par_unite = entrees["capacite_par_unite"]["valeur"]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    groupes = _par_sejour(lignes_mvt)
    evenements_par_unite: dict[str, list[tuple[datetime, int]]] = defaultdict(list)
    for lignes_du_sejour in groupes.values():
        lignes_triees = _lignes_avec_lit_triees(lignes_du_sejour)
        for indice, ligne in enumerate(lignes_triees):
            unite = ligne["service_accueil"] or ligne["service_destination"]
            debut = ligne["date_heure_admission"] or ligne["date_heure_mutation"]
            if indice + 1 < len(lignes_triees):
                suivante = lignes_triees[indice + 1]
                fin = suivante["date_heure_admission"] or suivante["date_heure_mutation"]
            else:
                fin = _fin_pour_calcul(lignes_du_sejour, date_fin)
            evenements_par_unite[unite].append((debut, 1))
            evenements_par_unite[unite].append((fin, -1))

    assert evenements_par_unite, "aucune unité à contrôler"
    for unite, evenements in evenements_par_unite.items():
        # meme regle de priorite qu'en 4 : un depart au meme instant qu'une arrivee
        # libere le lit avant qu'il ne soit repris.
        evenements_tries = sorted(evenements, key=lambda e: (e[0], e[1]))
        occ = 0
        max_occ = 0
        for _, delta in evenements_tries:
            occ += delta
            max_occ = max(max_occ, occ)
        assert max_occ <= capacite_par_unite[unite], (unite, max_occ, capacite_par_unite[unite])


def test_aucune_activite_chirurgicale(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]

    # controle positif : le motif recherche doit d'abord etre eprouve contre un libelle
    # fabrique connu pour le contenir, avant de conclure quoi que ce soit de son silence
    # sur les donnees reelles.
    motif = re.compile(r"chirurg", re.IGNORECASE)
    assert motif.search("Chirurgie générale"), "le motif ne detecte pas son propre cas positif"

    correspondance = entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    colonnes_codees = [c for c in correspondance if c["table"] == TABLE]

    valeurs_observees_par_nomenclature: dict[str, set[str]] = defaultdict(set)
    for correspondance_colonne in colonnes_codees:
        colonne = correspondance_colonne["colonne"]
        nom_nomenclature = correspondance_colonne["nomenclature"]
        for ligne in lignes_mvt:
            if ligne[colonne] is not None:
                valeurs_observees_par_nomenclature[nom_nomenclature].add(ligne[colonne])

    assert valeurs_observees_par_nomenclature, "aucune colonne codee observee a controler"
    for nom_nomenclature, codes in valeurs_observees_par_nomenclature.items():
        for code in codes:
            libelle = nomenclatures.libelle(nom_nomenclature, code, entrees)
            assert not motif.search(libelle), (nom_nomenclature, code, libelle)


# l'egalite de coherence urgences-hospitalisation et la part mesuree suivant le parametre
# pose sont verifiees par tests/test_coherence_inter_tables.py::test_regle_10... et
# test_regle_10_bis... (regles inter-tables du cadrage, deplacees depuis ce fichier).
