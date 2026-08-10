"""Contrôles propres à la table des passages (generator/passages.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement
(en-têtes, nomenclatures, bornage, horodatages non triviaux, colonne dégénérée, cohérence
intra-ligne, reproductibilité) : la bijection avec le fil des épisodes, le rattachement au
rendez-vous honoré, l'ordre des horodatages, les sorties manquantes et les durées par
catégorie. Génère par l'orchestrateur (generator/execution.py), pas en appelant
generator/passages.py directement, pour tester ce qui sera réellement produit.
"""

import statistics
from collections import Counter
from datetime import date

import pytest

from generator import volumes

TABLE = "source.passages"

PILOTES = {
    "H": "admissions_annuelles",
    "C": "consultations_specialisees_externes",
    "U": "passages_urgences_par_jour",
}


def patient_id_de(n_ipp: str) -> int:
    return int(n_ipp.split("-")[1])


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def test_bijection_avec_fil_des_episodes(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"][TABLE]

    comptes = {
        cat: volumes.comptes_journaliers(nom, entrees=entrees) for cat, nom in PILOTES.items()
    }
    attendu_par_categorie = {cat: sum(c.values()) for cat, c in comptes.items()}
    total_attendu = sum(attendu_par_categorie.values())

    assert len(lignes) == total_attendu

    mesure_par_type = Counter(ligne["type_passage"] for ligne in lignes)
    for categorie, attendu in attendu_par_categorie.items():
        assert mesure_par_type[categorie] == attendu, categorie


def test_rattachement_au_rendez_vous_honore(generation: dict) -> None:
    lignes_passages = generation["lignes"][TABLE]
    lignes_rdv = generation["lignes"]["source.rendez_vous"]

    honores = [ligne for ligne in lignes_rdv if ligne["etat"] == "HO"]
    n_rdv_honores = {ligne["n_rdv"] for ligne in honores}
    assert len(n_rdv_honores) == len(honores), "identifiant de rendez-vous honoré en double"

    passages_rattaches = [ligne for ligne in lignes_passages if ligne["n_rdv"] is not None]
    assert len(passages_rattaches) == len(honores)

    n_rdv_references = [ligne["n_rdv"] for ligne in passages_rattaches]
    assert len(n_rdv_references) == len(set(n_rdv_references)), "rendez-vous référencé deux fois"
    assert set(n_rdv_references) == n_rdv_honores, "un rendez-vous référencé n'existe pas"


def test_aucun_rattachement_indu(generation: dict) -> None:
    lignes = generation["lignes"][TABLE]

    non_consultations = [ligne for ligne in lignes if ligne["type_passage"] in ("H", "U")]
    assert non_consultations, "aucune ligne d'hospitalisation ni d'urgence à contrôler"
    assert all(ligne["n_rdv"] is None for ligne in non_consultations)
    assert all(ligne["activite"] is None for ligne in non_consultations)


def test_ordre_des_horodatages(generation: dict) -> None:
    lignes_passages = generation["lignes"][TABLE]
    lignes_patients = generation["lignes"]["source.patients"]

    fiche_par_patient: dict[int, date] = {}
    for ligne in lignes_patients:
        pid = patient_id_de(ligne["n_ipp"])
        fiche_par_patient.setdefault(pid, ligne["date_attribution"])

    assert lignes_passages, "aucune ligne de passage"
    for ligne in lignes_passages:
        pid = patient_id_de(ligne["n_ipp"])
        entree = ligne["date_heure_entree"]
        sortie = ligne["date_heure_sortie"]
        if sortie is not None:
            assert entree <= sortie, (ligne["n_passage"], entree, sortie)
        assert entree.date() >= fiche_par_patient[pid], (ligne["n_passage"], entree, pid)


def test_sorties_manquantes_pres_de_la_fin_de_periode(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"][TABLE]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    sans_sortie = [ligne for ligne in lignes if ligne["date_heure_sortie"] is None]
    assert len(sans_sortie) > 0

    # borne mesurée avant d'être écrite : sur la génération de mesure (graine 1), les
    # passages sans sortie sont tous des entrées des sept derniers jours de la période
    # (dms_publie ~ 6,6 jours) ; marge posée à 15 jours, plus du double de la médiane
    # d'hospitalisation, pour ne pas être fragile à une variation de graine.
    BORNE_JOURS = 15
    for ligne in sans_sortie:
        jours_avant_fin = (date_fin - ligne["date_heure_entree"].date()).days
        assert 0 <= jours_avant_fin <= BORNE_JOURS, (ligne["n_passage"], jours_avant_fin)


def test_duree_mediane_par_categorie(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"][TABLE]

    medianes_attendues = dict(entrees["duree_mediane_minutes_par_categorie"]["valeur"])
    medianes_attendues["H"] = entrees["dms_publie"]["valeur"] * 24 * 60

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 0 minute
    # (C, U) et 83,5 minutes (H, categorie a plus forte dispersion, mediane en jours)
    TOLERANCE_MINUTES = 200
    for categorie, mediane_attendue in medianes_attendues.items():
        durees = [
            (ligne["date_heure_sortie"] - ligne["date_heure_entree"]).total_seconds() / 60
            for ligne in lignes
            if ligne["type_passage"] == categorie and ligne["date_heure_sortie"] is not None
        ]
        assert len(durees) > 0
        mediane_mesuree = statistics.median(durees)
        assert abs(mediane_mesuree - mediane_attendue) < TOLERANCE_MINUTES, (
            categorie,
            mediane_attendue,
            mediane_mesuree,
        )
