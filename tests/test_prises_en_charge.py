"""Contrôles propres à la table des prises en charge (generator/prises_en_charge.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement : le
rattachement à une facture, l'éligibilité par couverture patient, l'accord entre part
organisme et prise en charge, la somme des parts, le taux par organisme, l'ordre des dates,
et le taux de refus. Consomme la génération partagée de tests/conftest.py.
"""

from collections import Counter
from datetime import date

import pytest

TABLE = "source.prises_en_charge"
TABLE_FACTURES = "source.factures"

TOLERANCE_TAUX = 0.02


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def test_rattachement(generation: dict) -> None:
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]

    n_episodes_factures = {f["n_episode"] for f in lignes_fac}
    assert lignes_pec, "aucune prise en charge à contrôler"

    n_episodes_avec_pec = [pec["n_episode"] for pec in lignes_pec]
    for pec in lignes_pec:
        assert pec["n_episode"] in n_episodes_factures, pec

    doublons = {ep for ep, n in Counter(n_episodes_avec_pec).items() if n > 1}
    assert not doublons, doublons


def test_eligibilite(generation: dict) -> None:
    lignes_pat = generation["lignes"]["source.patients"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]

    compagnie_par_ipp = {p["n_ipp"]: p["compagnie_assurance"] for p in lignes_pat}
    ipp_par_episode = {f["n_episode"]: f["n_ipp"] for f in lignes_fac}

    assert lignes_pec
    for pec in lignes_pec:
        n_ipp = ipp_par_episode[pec["n_episode"]]
        assert compagnie_par_ipp[n_ipp] != "SANS", pec


def test_part_organisme_accord_facture(generation: dict) -> None:
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]

    etat_par_episode = {pec["n_episode"]: pec["etat"] for pec in lignes_pec}
    factures_par_episode = {f["n_episode"]: f for f in lignes_fac}

    n_accordees = 0
    for pec in lignes_pec:
        if pec["etat"] != "O":
            continue
        n_accordees += 1
        facture = factures_par_episode[pec["n_episode"]]
        montant_attendu = round(facture["montant_total"] * pec["taux_prise_en_charge"], 2)
        assert facture["part_organisme"] == pytest.approx(montant_attendu), (pec, facture)

    assert n_accordees > 0, "aucune prise en charge accordée à contrôler"

    for facture in lignes_fac:
        etat = etat_par_episode.get(facture["n_episode"])
        if etat == "O":
            continue
        assert facture["part_organisme"] == 0.0, facture
        assert facture["part_patient"] == pytest.approx(facture["montant_total"]), facture


def test_somme_des_parts(generation: dict) -> None:
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    assert lignes_fac
    for facture in lignes_fac:
        assert facture["part_organisme"] + facture["part_patient"] == pytest.approx(
            facture["montant_total"]
        ), facture


def test_taux_par_organisme(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_pec = generation["lignes"][TABLE]
    taux_cfg = entrees["taux_couverture_par_organisme"]["valeur"]

    assert lignes_pec
    for pec in lignes_pec:
        assert pec["taux_prise_en_charge"] == taux_cfg[pec["organisme"]], pec


def test_ordre_des_dates(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]
    date_facture_par_episode = {f["n_episode"]: f["date_facture"] for f in lignes_fac}
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    # borne mesurée avant d'être écrite : le délai le plus long porté par
    # delai_jours_decision_prise_en_charge fixe le nombre de jours avant la fin de la
    # période au-delà duquel une demande ne peut plus jamais tomber en instance.
    delai_max = max(int(j) for j in entrees["delai_jours_decision_prise_en_charge"]["valeur"])

    assert lignes_pec
    n_instance = 0
    for pec in lignes_pec:
        date_facture = date_facture_par_episode[pec["n_episode"]]
        assert date_facture <= date_fin, pec
        if pec["date_verification"] is None:
            n_instance += 1
            assert (date_fin - date_facture).days < delai_max, pec
            continue
        assert pec["date_verification"].date() >= date_facture, pec

    assert n_instance > 0, "aucune demande en instance à contrôler"


def test_taux_de_refus(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_pec = generation["lignes"][TABLE]

    taux_cfg = entrees["taux_refus_prise_en_charge"]["valeur"]
    decidees = [pec for pec in lignes_pec if pec["etat"] in ("O", "F")]
    assert decidees, "aucune prise en charge décidée à contrôler"

    n_refusees = sum(1 for pec in decidees if pec["etat"] == "F")
    taux_mesure = n_refusees / len(decidees)
    assert abs(taux_mesure - taux_cfg) < TOLERANCE_TAUX, (taux_mesure, taux_cfg)

    motifs = entrees["motifs_refus_prise_en_charge"]["valeur"]
    assert abs(sum(motifs.values()) - 1.0) < 1e-9, motifs
