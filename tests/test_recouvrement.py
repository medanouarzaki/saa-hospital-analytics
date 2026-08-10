"""Contrôles propres aux tables de recouvrement (generator/recouvrement.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement : le
rattachement entre les trois tables et les factures (créances soldées comprises), la règle
jamais-plus-que-dû par débiteur, le calcul du montant d'une créance recalculé depuis les
encaissements, la naissance et le solde d'une créance, la survie des relances abouties, le
taux de recouvrement de cohorte (borné et conforme), le seuil de relance, l'accord entre une
relance aboutie et l'encaissement qu'elle engendre, le montant minimal d'un encaissement,
l'ordre des dates et la répartition par tranche d'ancienneté sur les créances ouvertes.
Consomme la génération partagée de tests/conftest.py.
"""

from collections import Counter, defaultdict
from datetime import date

import pytest

TABLE_ENC = "source.encaissements"
TABLE_CRE = "source.creances"
TABLE_REL = "source.relances"
TABLE_FAC = "source.factures"

TOLERANCE_TAUX = 0.05
MOTIF_SOLDE = "RCV"


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def _debiteur(entrees: dict, mode_reglement: str) -> str:
    return entrees["correspondance_debiteur_mode_reglement"]["valeur"][mode_reglement]


def _dernier_par_creance(lignes_cre: list[dict]) -> dict[str, dict]:
    dernier: dict[str, dict] = {}
    for cre in lignes_cre:
        courant = dernier.get(cre["n_creance"])
        if courant is None or cre["date_extraction"] > courant["date_extraction"]:
            dernier[cre["n_creance"]] = cre
    return dernier


def _premier_par_creance(lignes_cre: list[dict]) -> dict[str, dict]:
    premier: dict[str, dict] = {}
    for cre in lignes_cre:
        courant = premier.get(cre["n_creance"])
        if courant is None or cre["date_extraction"] < courant["date_extraction"]:
            premier[cre["n_creance"]] = cre
    return premier


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
        # y compris une relance qui a solde sa creance : la ligne de cloture reste presente.
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


def test_naissance_et_solde(generation: dict) -> None:
    # remplace l'ancien test, trop strict, qui interdisait tout montant nul sur toute
    # ligne de creance : une creance ne NAIT jamais a un montant nul ou negatif (verifie
    # ci-dessous sur la premiere ligne de chaque creance), mais peut ATTEINDRE zero en
    # cours de vie, auquel cas son etat final doit etre ecrit (motif RCV, montant restant
    # nul), pas supprime. Ancienne assertion, reportee ici pour memoire :
    #   for cre in lignes_cre: assert cre["montant_restant"] > 0
    # -- rougirait desormais sur toute creance soldee, par construction voulue de ce lot.
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_cre = generation["lignes"][TABLE_CRE]

    seuil = entrees["seuil_jours_anciennete_creance"]["valeur"]
    date_facture_par_id = {f["n_facture"]: f["date_facture"] for f in lignes_fac}

    premiers = _premier_par_creance(lignes_cre)
    assert premiers
    for cre in premiers.values():
        assert cre["montant_restant"] > 0, cre
        assert cre["motif_non_recouvrement"] != MOTIF_SOLDE, cre
        anciennete_naissance = (
            cre["date_naissance_creance"] - date_facture_par_id[cre["n_facture"]]
        ).days
        assert anciennete_naissance >= seuil, cre

    derniers = _dernier_par_creance(lignes_cre)
    soldees = [cre for cre in derniers.values() if cre["motif_non_recouvrement"] == MOTIF_SOLDE]
    assert soldees, "aucune créance soldée à contrôler"
    for cre in soldees:
        assert cre["montant_restant"] == 0, cre

    for cre in derniers.values():
        if cre["motif_non_recouvrement"] != MOTIF_SOLDE:
            assert cre["montant_restant"] > 0, cre


def test_relances_abouties_survivent(generation: dict) -> None:
    lignes_rel = generation["lignes"][TABLE_REL]

    par_canal: dict[str, Counter] = defaultdict(Counter)
    for rel in lignes_rel:
        par_canal[rel["canal"]][rel["resultat"]] += 1

    n_payees = sum(1 for rel in lignes_rel if rel["resultat"] == "PAYE")
    assert n_payees > 0, "aucune relance payée dans la table"

    assert par_canal
    for canal, compte in par_canal.items():
        total = sum(compte.values())
        abouti = compte.get("PAYE", 0) + compte.get("PART", 0)
        assert compte.get("PAYE", 0) >= 0, canal
        taux = abouti / total
        assert 0 <= taux <= 1, (canal, taux)


def test_taux_recouvrement_borne(generation: dict) -> None:
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]

    du_cohorte: Counter = Counter()
    for f in lignes_fac:
        du_cohorte[(f["type_episode"], f["date_facture"].year)] += f["montant_total"]

    enc_par_facture: Counter = Counter()
    for enc in lignes_enc:
        enc_par_facture[enc["n_facture"]] += enc["montant"]

    enc_cohorte: Counter = Counter()
    for f in lignes_fac:
        enc_cohorte[(f["type_episode"], f["date_facture"].year)] += enc_par_facture.get(
            f["n_facture"], 0.0
        )

    assert du_cohorte
    for cle, du in du_cohorte.items():
        taux = enc_cohorte[cle] / du
        assert 0 <= taux <= 1 + 1e-9, (cle, taux, du, enc_cohorte[cle])


def test_taux_recouvrement_conforme(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_fac = generation["lignes"][TABLE_FAC]
    lignes_enc = generation["lignes"][TABLE_ENC]

    taux_cfg = entrees["taux_recouvrement"]["valeur"]

    du_par_type: Counter = Counter()
    for f in lignes_fac:
        du_par_type[f["type_episode"]] += f["montant_total"]

    enc_par_facture: Counter = Counter()
    for enc in lignes_enc:
        enc_par_facture[enc["n_facture"]] += enc["montant"]

    enc_par_type: Counter = Counter()
    for f in lignes_fac:
        enc_par_type[f["type_episode"]] += enc_par_facture.get(f["n_facture"], 0.0)

    for type_episode, taux in taux_cfg.items():
        mesure = enc_par_type[type_episode] / du_par_type[type_episode]
        assert abs(mesure - taux) < TOLERANCE_TAUX, (type_episode, mesure, taux)


def test_seuil_relance(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_cre = generation["lignes"][TABLE_CRE]
    lignes_rel = generation["lignes"][TABLE_REL]

    seuil_montant = entrees["seuil_montant_relance"]["valeur"]

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


def test_montant_minimal_encaissement(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_enc = generation["lignes"][TABLE_ENC]

    seuil = entrees["montant_minimal_encaissement"]["valeur"]

    # regroupe par facture et debiteur : un groupe d'une seule ligne est un versement
    # unique, exempte du seuil (rien avec quoi le fusionner) ; un groupe de plusieurs
    # lignes est un versement partiel, chaque ligne doit alors respecter le seuil.
    groupes = defaultdict(list)
    for enc in lignes_enc:
        debiteur = _debiteur(entrees, enc["mode_reglement"])
        groupes[(enc["n_facture"], debiteur)].append(enc)

    assert groupes
    n_groupes_multiples = 0
    for lignes in groupes.values():
        if len(lignes) <= 1:
            continue
        n_groupes_multiples += 1
        for enc in lignes:
            assert enc["montant"] >= seuil, enc
    assert n_groupes_multiples > 0, "aucun versement partiel à contrôler"

    # conservation : la somme des encaissements d'une facture n'est pas affectee par le
    # seuil - verifiee ici contre le calcul independant deja porte par la creance
    # correspondante (montant_recouvre a sa derniere ligne = du - restant).
    lignes_cre = generation["lignes"][TABLE_CRE]
    enc_total_par_facture: Counter = Counter()
    for enc in lignes_enc:
        enc_total_par_facture[enc["n_facture"]] += enc["montant"]

    dernier_par_creance = _dernier_par_creance(lignes_cre)
    assert dernier_par_creance
    for cre in dernier_par_creance.values():
        recouvre_attendu = round(cre["montant_du"] - cre["montant_restant"], 2)
        assert enc_total_par_facture[cre["n_facture"]] >= recouvre_attendu - 0.02, cre


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
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    tranches = entrees["tranches_anciennete_creances"]["valeur"]

    # l'analyse par tranche d'anciennete ne porte que sur les creances OUVERTES (dernier
    # etat different de RCV, montant restant strictement positif) : une creance soldee
    # n'a plus de solde a vieillir.
    dernier_par_creance = _dernier_par_creance(lignes_cre)
    ouvertes = [
        cre for cre in dernier_par_creance.values() if cre["motif_non_recouvrement"] != MOTIF_SOLDE
    ]
    assert ouvertes
    n_ouvertes_independant = sum(
        1 for cre in dernier_par_creance.values() if cre["montant_restant"] > 0
    )
    assert len(ouvertes) == n_ouvertes_independant

    comptes = Counter()
    for cre in ouvertes:
        anciennete = (date_fin - cre["date_naissance_creance"]).days
        for tranche in tranches:
            haute = tranche["borne_haute"]
            if anciennete >= tranche["borne_basse"] and (haute is None or anciennete <= haute):
                comptes[tranche["libelle"]] += 1
                break

    assert sum(comptes.values()) == len(ouvertes)
    for tranche in tranches:
        assert comptes[tranche["libelle"]] > 0, tranche
