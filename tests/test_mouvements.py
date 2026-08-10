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

from generator import mouvements as mvt_mod
from generator import nomenclatures

TABLE = "source.mouvements"


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


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


def test_journees_hospitalisation(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    lignes_passages = generation["lignes"]["source.passages"]
    lignes_h = [ligne for ligne in lignes_passages if ligne["type_passage"] == "H"]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    groupes = _par_sejour(lignes_mvt)
    journees_par_annee: dict[int, float] = defaultdict(float)
    for lignes_du_sejour in groupes.values():
        admission = _admission(lignes_du_sejour)["date_heure_admission"]
        fin = _fin_pour_calcul(lignes_du_sejour, date_fin)
        duree_jours = (fin - admission).total_seconds() / 86400
        if admission.year == fin.year:
            journees_par_annee[admission.year] += duree_jours
        else:
            fin_annee = date(admission.year, 12, 31)
            jours_annee_admission = (fin_annee - admission.date()).days + 1
            journees_par_annee[admission.year] += min(jours_annee_admission, duree_jours)
            reste = duree_jours - jours_annee_admission
            if reste > 0:
                journees_par_annee[fin.year] += reste

    total_mesure = sum(journees_par_annee.values())
    cible = mvt_mod._duree_moyenne_cible_jours(lignes_h, entrees) * len(lignes_h)

    # tolerance mesuree sur 3 graines independantes : ecart relatif maximal observe 0,68 %
    TOLERANCE_RELATIVE = 0.02
    assert abs(total_mesure - cible) / cible < TOLERANCE_RELATIVE, (total_mesure, cible)


def test_duree_moyenne_de_sejour(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    lignes_passages = generation["lignes"]["source.passages"]
    lignes_h = [ligne for ligne in lignes_passages if ligne["type_passage"] == "H"]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    groupes = _par_sejour(lignes_mvt)
    durees = []
    for lignes_du_sejour in groupes.values():
        admission = _admission(lignes_du_sejour)["date_heure_admission"]
        fin = _fin_pour_calcul(lignes_du_sejour, date_fin)
        durees.append((fin - admission).total_seconds() / 86400)

    dms_mesuree = sum(durees) / len(durees)
    dms_cible = mvt_mod._duree_moyenne_cible_jours(lignes_h, entrees)
    dms_publiee = entrees["dms_publie"]["valeur"]

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 0,044 jour
    # entre duree moyenne mesuree et cible imposee (journees / admissions)
    TOLERANCE_JOURS = 0.15
    assert abs(dms_mesuree - dms_cible) < TOLERANCE_JOURS, (dms_mesuree, dms_cible, dms_publiee)


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

    evenements.sort(key=lambda e: (e[0], -e[1]))
    occ = 0
    max_occ = 0
    for _, delta in evenements:
        occ += delta
        max_occ = max(max_occ, occ)

    assert max_occ <= capacite, (max_occ, capacite)


def test_taux_occupation(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_mvt = generation["lignes"][TABLE]
    capacite = entrees["capacite_litiere_fonctionnelle"]["valeur"]
    tom_publie = entrees["tom_publie"]["valeur"]
    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    n_jours_periode = (date_fin - date_debut).days + 1

    groupes = _par_sejour(lignes_mvt)
    total_journees = 0.0
    for lignes_du_sejour in groupes.values():
        admission = _admission(lignes_du_sejour)["date_heure_admission"]
        fin = _fin_pour_calcul(lignes_du_sejour, date_fin)
        total_journees += (fin - admission).total_seconds() / 86400

    tom_mesure = total_journees / (capacite * n_jours_periode) * 100

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 0,59 point
    TOLERANCE_POINTS = 1.5
    assert abs(tom_mesure - tom_publie) < TOLERANCE_POINTS, (tom_mesure, tom_publie)


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


def test_ordre_des_horodatages(generation: dict) -> None:
    lignes_mvt = generation["lignes"][TABLE]
    groupes = _par_sejour(lignes_mvt)

    assert groupes, "aucun séjour à contrôler"
    for lignes_du_sejour in groupes.values():
        admission = _admission(lignes_du_sejour)["date_heure_admission"]
        mutations = [
            ligne["date_heure_mutation"]
            for ligne in lignes_du_sejour
            if ligne["date_heure_mutation"] is not None
        ]
        sortie = _sortie(lignes_du_sejour)

        if mutations:
            assert admission < mutations[0], (admission, mutations[0])
        if sortie is not None:
            derniere_reference = mutations[0] if mutations else admission
            assert derniere_reference < sortie, (derniere_reference, sortie)


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
