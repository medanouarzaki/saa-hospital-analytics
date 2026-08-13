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
    # date_facture ancre l'evenement : une fiche a compagnie_assurance modifiable
    # (generator/patients.py::COLONNES_PAR_TYPE_MODIFICATION), l'eligibilite se juge sur la
    # couverture en vigueur au moment de la facture, pas sur la derniere version reextraite
    # -- sans quoi une PEC correctement accordee avant un changement de couverture vers SANS
    # ferait rougir ce test a tort (mesure au lot qui a introduit ce changement, voir le
    # rapport).
    lignes_pat = generation["lignes"]["source.patients"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]

    versions_par_ipp: dict[str, list[dict]] = {}
    for ligne in lignes_pat:
        versions_par_ipp.setdefault(ligne["n_ipp"], []).append(ligne)

    def compagnie_en_vigueur(n_ipp: str, jour: date) -> str:
        versions_triees = sorted(versions_par_ipp[n_ipp], key=lambda v: v["date_extraction"])
        candidates = [v for v in versions_triees if v["date_extraction"] <= jour]
        version = candidates[-1] if candidates else versions_triees[0]
        return version["compagnie_assurance"]

    facture_par_episode = {f["n_episode"]: f for f in lignes_fac}

    assert lignes_pec
    for pec in lignes_pec:
        facture = facture_par_episode[pec["n_episode"]]
        assert compagnie_en_vigueur(facture["n_ipp"], facture["date_facture"]) != "SANS", pec


def test_pec_utilise_version_en_vigueur_a_la_date_facture(generation: dict) -> None:
    """Pour chaque facture d'un patient à versions multiples, la présence d'une prise en
    charge et son organisme correspondent à la couverture de la version en vigueur à
    `date_facture`, pas à la dernière version réextraite. Recalcul entièrement réécrit ici,
    indépendant de `generator/patients.py::version_en_vigueur`."""
    entrees = generation["entrees"]
    lignes_pat = generation["lignes"]["source.patients"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]
    correspondance_regime = entrees["correspondance_regime_compagnie_assurance"]["valeur"]

    versions_par_ipp: dict[str, list[dict]] = {}
    for ligne in lignes_pat:
        versions_par_ipp.setdefault(ligne["n_ipp"], []).append(ligne)

    def version_en_vigueur(n_ipp: str, jour: date) -> dict:
        versions_triees = sorted(versions_par_ipp[n_ipp], key=lambda v: v["date_extraction"])
        candidates = [v for v in versions_triees if v["date_extraction"] <= jour]
        return candidates[-1] if candidates else versions_triees[0]

    factures_multi = [f for f in lignes_fac if len(versions_par_ipp.get(f["n_ipp"], [])) == 2]

    # anti-vacuite : au moins une facture doit "voir" une compagnie differente selon qu'on
    # prenne la derniere version reextraite ou la version en vigueur a sa date -- sans quoi
    # les assertions ci-dessous seraient satisfaites par vacuite (aucun cas ne distinguant
    # les deux semantiques).
    n_cas_discriminants = 0
    for f in factures_multi:
        derniere = max(versions_par_ipp[f["n_ipp"]], key=lambda v: v["date_extraction"])
        en_vigueur = version_en_vigueur(f["n_ipp"], f["date_facture"])
        if derniere["compagnie_assurance"] != en_vigueur["compagnie_assurance"]:
            n_cas_discriminants += 1
    assert n_cas_discriminants > 0, "aucun cas discriminant : le test serait vrai par vacuité"

    pec_par_episode = {pec["n_episode"]: pec for pec in lignes_pec}

    for f in factures_multi:
        version_attendue = version_en_vigueur(f["n_ipp"], f["date_facture"])
        compagnie_attendue = version_attendue["compagnie_assurance"]
        pec = pec_par_episode.get(f["n_episode"])
        if compagnie_attendue == "SANS":
            assert pec is None, (f, pec, "SANS ne doit jamais produire de PEC")
        elif pec is not None:
            assert pec["organisme"] == correspondance_regime[compagnie_attendue], (f, pec)


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


# part organisme + part patient == total (regle inter-tables du cadrage) est verifie par
# tests/test_coherence_inter_tables.py::test_regle_04..., deplacee depuis ce fichier.


def test_taux_selon_type_et_seuil(generation: dict) -> None:
    # remplace test_taux_par_organisme (lot precedent) : le taux de prise en charge ne
    # depend plus de l'organisme mais du type d'episode et, en ambulatoire, d'un seuil de
    # montant (regle S-18).
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_pec = generation["lignes"][TABLE]

    taux_hos = entrees["taux_part_organisme_hospitalisation"]["valeur"]
    taux_ambu_haut = entrees["taux_part_organisme_ambulatoire_haut"]["valeur"]
    seuil = entrees["seuil_dirhams_part_organisme_ambulatoire"]["valeur"]
    facture_par_episode = {f["n_episode"]: f for f in lignes_fac}

    assert lignes_pec
    n_hos = n_ambu_haut = n_ambu_bas = 0
    for pec in lignes_pec:
        facture = facture_par_episode[pec["n_episode"]]
        if pec["type_episode"] == "HOS":
            assert pec["taux_prise_en_charge"] == taux_hos, pec
            n_hos += 1
        elif facture["montant_total"] > seuil:
            assert pec["taux_prise_en_charge"] == taux_ambu_haut, pec
            n_ambu_haut += 1
        else:
            assert pec["taux_prise_en_charge"] == 0.0, pec
            n_ambu_bas += 1

    assert n_hos > 0, "aucune prise en charge d'hospitalisation à contrôler"
    assert n_ambu_haut > 0, "aucune prise en charge ambulatoire au-dessus du seuil à contrôler"
    assert n_ambu_bas > 0, "aucune prise en charge ambulatoire sous le seuil à contrôler"


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
