"""Contrôles propres aux tables de recouvrement (generator/recouvrement.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement : le
rattachement entre les trois tables et les factures, la règle jamais-plus-que-dû par
débiteur, le calcul du montant d'une créance recalculé depuis les encaissements, l'absence
de créance sur une facture soldée, le taux de recouvrement par type d'épisode, le seuil de
relance, l'accord entre une relance aboutie et l'encaissement qu'elle engendre, l'ordre des
dates et la répartition par tranche d'ancienneté. Consomme la génération partagée de
tests/conftest.py.
"""

from collections import Counter, defaultdict

import pytest

TABLE_ENC = "source.encaissements"
TABLE_CRE = "source.creances"
TABLE_REL = "source.relances"
TABLE_FAC = "source.factures"

TOLERANCE_TAUX = 0.05


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def _debiteur(entrees: dict, mode_reglement: str) -> str:
    return entrees["correspondance_debiteur_mode_reglement"]["valeur"][mode_reglement]


def test_rattachement(generation: dict) -> None:
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]
    lignes_cre = generation["lignes"][TABLE_CRE]
    lignes_rel = generation["lignes"][TABLE_REL]

    n_factures = {f["n_facture"] for f in lignes_fac}
    n_creances = {c["n_creance"] for c in lignes_cre}

    assert lignes_enc and lignes_cre and lignes_rel

    for enc in lignes_enc:
        assert enc["n_facture"] in n_factures, enc
    for cre in lignes_cre:
        assert cre["n_facture"] in n_factures, cre
    for rel in lignes_rel:
        assert rel["n_creance"] in n_creances, rel


def test_jamais_plus_que_du(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]

    dus = {f["n_facture"]: (f["part_patient"], f["part_organisme"]) for f in lignes_fac}
    encaisse = defaultdict(lambda: {"PATIENT": 0.0, "ORGANISME": 0.0})
    for enc in lignes_enc:
        debiteur = _debiteur(entrees, enc["mode_reglement"])
        encaisse[enc["n_facture"]][debiteur] += enc["montant"]

    assert encaisse
    for n_facture, (du_patient, du_organisme) in dus.items():
        e = encaisse[n_facture]
        assert e["PATIENT"] <= du_patient + 0.02, (n_facture, e["PATIENT"], du_patient)
        assert e["ORGANISME"] <= du_organisme + 0.02, (n_facture, e["ORGANISME"], du_organisme)


def test_montant_creance_se_calcule(generation: dict) -> None:
    lignes_cre = generation["lignes"][TABLE_CRE]
    lignes_enc = generation["lignes"][TABLE_ENC]

    enc_par_facture = defaultdict(list)
    for enc in lignes_enc:
        enc_par_facture[enc["n_facture"]].append(enc)

    assert lignes_cre
    for cre in lignes_cre:
        recouvre_attendu = round(
            sum(
                e["montant"]
                for e in enc_par_facture[cre["n_facture"]]
                if e["date_encaissement"].date() <= cre["date_extraction"]
            ),
            2,
        )
        assert cre["montant_recouvre"] == pytest.approx(recouvre_attendu, abs=0.02), cre
        restant_attendu = round(cre["montant_du"] - recouvre_attendu, 2)
        assert cre["montant_restant"] == pytest.approx(restant_attendu, abs=0.02), cre


def test_aucune_creance_sans_solde(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]
    lignes_cre = generation["lignes"][TABLE_CRE]

    seuil = entrees["seuil_jours_anciennete_creance"]["valeur"]
    enc_total_par_facture = defaultdict(float)
    for enc in lignes_enc:
        enc_total_par_facture[enc["n_facture"]] += enc["montant"]

    n_creances_par_facture = {cre["n_facture"] for cre in lignes_cre}
    for f in lignes_fac:
        if enc_total_par_facture[f["n_facture"]] >= round(f["montant_total"], 2) - 0.02:
            assert f["n_facture"] not in n_creances_par_facture, f

    assert lignes_cre
    for cre in lignes_cre:
        assert cre["montant_restant"] > 0, cre
        assert (cre["date_naissance_creance"] - _date_facture(lignes_fac, cre)).days >= seuil, cre


def _date_facture(lignes_fac: list[dict], cre: dict):
    for f in lignes_fac:
        if f["n_facture"] == cre["n_facture"]:
            return f["date_facture"]
    raise KeyError(cre["n_facture"])


def test_taux_recouvrement_par_type_episode(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]

    taux_cfg = entrees["taux_recouvrement"]["valeur"]
    type_par_facture = {f["n_facture"]: f["type_episode"] for f in lignes_fac}
    du_par_type: Counter = Counter()
    for f in lignes_fac:
        du_par_type[f["type_episode"]] += f["montant_total"]
    encaisse_par_type: Counter = Counter()
    for enc in lignes_enc:
        encaisse_par_type[type_par_facture[enc["n_facture"]]] += enc["montant"]

    for type_episode, taux in taux_cfg.items():
        mesure = encaisse_par_type[type_episode] / du_par_type[type_episode]
        assert abs(mesure - taux) < TOLERANCE_TAUX, (type_episode, mesure, taux)


def test_seuil_relance(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_cre = generation["lignes"][TABLE_CRE]
    lignes_rel = generation["lignes"][TABLE_REL]

    seuil_montant = entrees["seuil_montant_relance"]["valeur"]

    # etat de la creance a la date de chaque relance : le dernier instantane de creance
    # dont la date d'extraction precede STRICTEMENT la date de relance - un instantane
    # date le meme jour que la relance est sa propre consequence (l'encaissement qu'une
    # relance aboutie engendre est date le jour meme), pas son etat prealable.
    lignes_cre_par_creance = defaultdict(list)
    for cre in lignes_cre:
        lignes_cre_par_creance[cre["n_creance"]].append(cre)
    for liste in lignes_cre_par_creance.values():
        liste.sort(key=lambda c: c["date_extraction"])

    assert lignes_rel
    for rel in lignes_rel:
        instantanes = lignes_cre_par_creance[rel["n_creance"]]
        precedents = [c for c in instantanes if c["date_extraction"] < rel["date_relance"]]
        assert precedents, rel
        etat = precedents[-1]
        assert etat["montant_restant"] >= seuil_montant, (rel, etat)


def test_relances_encaissements_saccordent(generation: dict) -> None:
    lignes_rel = generation["lignes"][TABLE_REL]
    lignes_cre = generation["lignes"][TABLE_CRE]
    lignes_enc = generation["lignes"][TABLE_ENC]

    facture_par_creance = {cre["n_creance"]: cre["n_facture"] for cre in lignes_cre}
    dates_encaissement_par_facture = defaultdict(set)
    for enc in lignes_enc:
        dates_encaissement_par_facture[enc["n_facture"]].add(enc["date_encaissement"].date())

    relances_abouties = [rel for rel in lignes_rel if rel["resultat"] in ("PAYE", "PART")]
    assert relances_abouties, "aucune relance aboutie à contrôler"
    for rel in relances_abouties:
        n_facture = facture_par_creance[rel["n_creance"]]
        assert rel["date_relance"] in dates_encaissement_par_facture[n_facture], rel


def test_ordre_des_dates(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]
    lignes_cre = generation["lignes"][TABLE_CRE]
    lignes_rel = generation["lignes"][TABLE_REL]

    date_facture_par_id = {f["n_facture"]: f["date_facture"] for f in lignes_fac}
    seuil = entrees["seuil_jours_anciennete_creance"]["valeur"]
    delai_relances = entrees["delai_jours_entre_relances"]["valeur"]

    assert lignes_enc
    for enc in lignes_enc:
        assert enc["date_encaissement"].date() >= date_facture_par_id[enc["n_facture"]], enc

    assert lignes_cre
    for cre in lignes_cre:
        assert (
            cre["date_naissance_creance"] - date_facture_par_id[cre["n_facture"]]
        ).days >= seuil, cre

    naissance_par_creance = {cre["n_creance"]: cre["date_naissance_creance"] for cre in lignes_cre}
    relances_par_creance = defaultdict(list)
    for rel in lignes_rel:
        relances_par_creance[rel["n_creance"]].append(rel["date_relance"])

    assert relances_par_creance
    for n_creance, dates in relances_par_creance.items():
        naissance = naissance_par_creance[n_creance]
        for d in dates:
            assert d > naissance, (n_creance, d, naissance)
        dates_triees = sorted(dates)
        assert len(set(dates)) == len(dates), (n_creance, dates)
        for precedente, suivante in zip(dates_triees, dates_triees[1:], strict=False):
            assert (suivante - precedente).days >= delai_relances, (n_creance, precedente, suivante)


def test_repartition_anciennete(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_cre = generation["lignes"][TABLE_CRE]
    date_fin_str = entrees["date_fin"]["valeur"]

    from datetime import date

    date_fin = date.fromisoformat(date_fin_str)
    tranches = entrees["tranches_anciennete_creances"]["valeur"]

    # derniere ligne de chaque creance = son etat courant
    dernier_par_creance: dict[str, dict] = {}
    for cre in lignes_cre:
        courant = dernier_par_creance.get(cre["n_creance"])
        if courant is None or cre["date_extraction"] > courant["date_extraction"]:
            dernier_par_creance[cre["n_creance"]] = cre

    comptes = Counter()
    for cre in dernier_par_creance.values():
        anciennete = (date_fin - cre["date_naissance_creance"]).days
        for tranche in tranches:
            haute = tranche["borne_haute"]
            if anciennete >= tranche["borne_basse"] and (haute is None or anciennete <= haute):
                comptes[tranche["libelle"]] += 1
                break

    assert dernier_par_creance
    for tranche in tranches:
        assert comptes[tranche["libelle"]] > 0, tranche
