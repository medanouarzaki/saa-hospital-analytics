"""Contrôles propres aux tables de facturation (generator/facturation.py).

Ne porte que ce que tests/test_invariants_tables.py ne couvre pas déjà génériquement : le
taux de facturation, le rattachement facture/ligne/épisode, la numérotation des lignes, les
volumes de laboratoire par catégorie, le ratio d'examens par prélèvement, la cohérence des
journées facturées avec la table des mouvements, le calcul des montants, l'absence d'actes
interdits, l'ordre des dates et la provenance de la tarification. Consomme la génération
partagée de tests/conftest.py.
"""

import re
from collections import Counter
from datetime import timedelta

import pytest

from generator import facturation

TABLE_FACTURES = "source.factures"
TABLE_LIGNES = "source.lignes_facture"

TERMES_INTERDITS = ["chirurg", "bactério", "bacterio", "parasito", "hygiène aliment"]

TOLERANCE_TAUX = 0.02
TOLERANCE_RATIO = 0.02

# Correspondance structurelle type_passage -> type_episode (pas les taux eux-memes, lus
# depuis la configuration par le test).
CORRESPONDANCE_TYPE_PASSAGE = {"H": "HOS", "C": "CE", "U": "UR"}


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def test_taux_facturation_par_type_episode(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_pas = generation["lignes"]["source.passages"]
    lignes_urg = generation["lignes"]["source.passages_urgences"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]

    taux_cfg = entrees["taux_facturation"]["valeur"]
    orientations = {u["n_passage"]: u["orientation_sortie"] for u in lignes_urg}
    n_factures_par_type = Counter(f["type_episode"] for f in lignes_fac)

    for code_passage, type_episode in CORRESPONDANCE_TYPE_PASSAGE.items():
        episodes = [p for p in lignes_pas if p["type_passage"] == code_passage]
        if type_episode == "UR":
            episodes = [p for p in episodes if orientations.get(p["n_passage"]) != "HO"]
        n_eligibles = len(episodes)
        taux_mesure = n_factures_par_type.get(type_episode, 0) / n_eligibles
        assert abs(taux_mesure - taux_cfg[type_episode]) < TOLERANCE_TAUX, (
            type_episode,
            taux_mesure,
            taux_cfg[type_episode],
        )


def test_urgences_facturees(generation: dict) -> None:
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_lig = generation["lignes"][TABLE_LIGNES]

    factures_ur = {f["n_facture"] for f in lignes_fac if f["type_episode"] == "UR"}
    assert len(factures_ur) > 0

    montant_ur = sum(ligne["montant"] for ligne in lignes_lig if ligne["n_facture"] in factures_ur)
    assert montant_ur > 0


def test_aucune_double_facturation_urgences_hospitalisation(generation: dict) -> None:
    lignes_urg = generation["lignes"]["source.passages_urgences"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]

    n_passages_ho = {u["n_passage"] for u in lignes_urg if u["orientation_sortie"] == "HO"}
    assert n_passages_ho, "aucun passage oriente vers l'hospitalisation a controler"

    n_episodes_ur_factures = {f["n_episode"] for f in lignes_fac if f["type_episode"] == "UR"}
    assert n_episodes_ur_factures.isdisjoint(n_passages_ho)


def test_rattachement(generation: dict) -> None:
    lignes_pas = generation["lignes"]["source.passages"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_lig = generation["lignes"][TABLE_LIGNES]

    n_episodes = {p["n_passage"] for p in lignes_pas}
    n_factures = {f["n_facture"] for f in lignes_fac}

    assert lignes_fac, "aucune facture à contrôler"
    assert lignes_lig, "aucune ligne à contrôler"

    for facture in lignes_fac:
        assert facture["n_episode"] in n_episodes, facture

    factures_avec_ligne = {ligne["n_facture"] for ligne in lignes_lig}
    assert factures_avec_ligne == n_factures, (
        "sans ligne",
        n_factures - factures_avec_ligne,
        "orphelines",
        factures_avec_ligne - n_factures,
    )

    for ligne in lignes_lig:
        assert ligne["n_facture"] in n_factures, ligne


def test_numerotation(generation: dict) -> None:
    lignes_lig = generation["lignes"][TABLE_LIGNES]
    par_facture: dict[str, list[int]] = {}
    for ligne in lignes_lig:
        par_facture.setdefault(ligne["n_facture"], []).append(ligne["n_ligne"])

    assert par_facture
    for n_facture, rangs in par_facture.items():
        assert sorted(rangs) == list(range(1, len(rangs) + 1)), (n_facture, sorted(rangs))


def test_volumes_laboratoire(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_lig = generation["lignes"][TABLE_LIGNES]

    from generator import volumes

    correspondance = {
        "immuno_serologie": ("LAB-IS-", "examens_immuno_serologie"),
        "hematologie_transfusion": ("LAB-HT-", "examens_hematologie_transfusion"),
        "chimie_biologie": ("LAB-CB-", "examens_chimie_biologie"),
    }
    for categorie, (prefixe, nom_volume) in correspondance.items():
        cible = sum(volumes.comptes_journaliers(nom_volume, entrees=entrees).values())
        mesure = sum(1 for ligne in lignes_lig if ligne["code_acte"].startswith(prefixe))
        assert mesure == cible, (categorie, mesure, cible)


def test_ratio_examens_par_prelevement(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_lig = generation["lignes"][TABLE_LIGNES]
    ratio_cfg = entrees["ratio_examens_par_prelevement"]["valeur"]

    lignes_b = [ligne for ligne in lignes_lig if ligne["lettre_cle"] == "B"]
    groupes: dict[tuple[str, object], int] = {}
    for ligne in lignes_b:
        cle = (ligne["n_facture"], ligne["date_acte"])
        groupes[cle] = groupes.get(cle, 0) + 1

    assert groupes
    ratio_mesure = len(lignes_b) / len(groupes)
    assert abs(ratio_mesure - ratio_cfg) < TOLERANCE_RATIO, (ratio_mesure, ratio_cfg)


def test_journees_facturees(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_pas = generation["lignes"]["source.passages"]
    lignes_mvt = generation["lignes"]["source.mouvements"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_lig = generation["lignes"][TABLE_LIGNES]

    from datetime import date

    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    sejours_par_passage = facturation._construire_sejours(lignes_pas, lignes_mvt, date_fin)

    n_episodes_hos_factures = {f["n_episode"] for f in lignes_fac if f["type_episode"] == "HOS"}
    assert n_episodes_hos_factures

    total_independant = sum(
        sejours_par_passage[n_passage]["n_journees"] for n_passage in n_episodes_hos_factures
    )
    n_lignes_journee = sum(1 for ligne in lignes_lig if ligne["code_acte"] == "HOSP-J")

    assert n_lignes_journee == total_independant, (n_lignes_journee, total_independant)


def test_montants(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_lig = generation["lignes"][TABLE_LIGNES]
    lignes_fac = generation["lignes"][TABLE_FACTURES]

    valeurs_lettres = {
        lettre["code"]: lettre["valeur_unitaire"]
        for lettre in entrees["nomenclature_lettres_cles"]["valeur"]
    }
    actes_par_code = {acte["code"]: acte for acte in entrees["nomenclature_actes"]["valeur"]}

    assert lignes_lig
    for ligne in lignes_lig:
        acte = actes_par_code[ligne["code_acte"]]
        attendu = valeurs_lettres[acte["lettre_cle"]] * acte["coefficient"] * ligne["quantite"]
        assert ligne["montant"] == pytest.approx(attendu), (
            ligne["code_acte"],
            ligne["montant"],
            attendu,
        )

    montants_par_facture: dict[str, float] = {}
    for ligne in lignes_lig:
        montants_par_facture[ligne["n_facture"]] = (
            montants_par_facture.get(ligne["n_facture"], 0.0) + ligne["montant"]
        )

    assert lignes_fac
    for facture in lignes_fac:
        attendu = round(montants_par_facture[facture["n_facture"]], 2)
        assert facture["montant_total"] == pytest.approx(attendu), (
            facture["n_facture"],
            facture["montant_total"],
            attendu,
        )


def test_aucun_acte_interdit(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_lig = generation["lignes"][TABLE_LIGNES]

    motif = re.compile(r"chirurg|bactério|bacterio|parasito|hygiène aliment", re.IGNORECASE)
    assert motif.search("Cure de hernie inguinale (chirurgie générale)"), (
        "le motif ne détecte pas son propre cas positif"
    )

    libelles = {acte["libelle"] for acte in entrees["nomenclature_actes"]["valeur"]}
    assert libelles
    for libelle in libelles:
        for terme in TERMES_INTERDITS:
            assert terme not in libelle.lower(), (libelle, terme)

    libelles_lignes = {ligne["libelle_acte"] for ligne in lignes_lig}
    assert libelles_lignes
    for libelle in libelles_lignes:
        for terme in TERMES_INTERDITS:
            assert terme not in libelle.lower(), (libelle, terme)


def test_ordre_des_dates(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes_pas = generation["lignes"]["source.passages"]
    lignes_mvt = generation["lignes"]["source.mouvements"]
    lignes_fac = generation["lignes"][TABLE_FACTURES]
    lignes_lig = generation["lignes"][TABLE_LIGNES]

    from datetime import date

    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    sejours_par_passage = facturation._construire_sejours(lignes_pas, lignes_mvt, date_fin)
    passages_par_id = {p["n_passage"]: p for p in lignes_pas}

    dates_facture = {f["n_facture"]: f["date_facture"] for f in lignes_fac}
    episode_par_facture = {f["n_facture"]: f["n_episode"] for f in lignes_fac}
    type_par_facture = {f["n_facture"]: f["type_episode"] for f in lignes_fac}

    assert lignes_lig
    for ligne in lignes_lig:
        n_facture = ligne["n_facture"]
        n_episode = episode_par_facture[n_facture]
        type_episode = type_par_facture[n_facture]

        if type_episode == "HOS":
            sejour = sejours_par_passage[n_episode]
            borne_min = sejour["entree"].date()
            borne_max = borne_min + timedelta(days=sejour["n_journees"] - 1)
        else:
            borne_min = borne_max = passages_par_id[n_episode]["date_heure_entree"].date()

        assert borne_min <= ligne["date_acte"] <= borne_max, (ligne, borne_min, borne_max)
        assert dates_facture[n_facture] >= ligne["date_acte"], (ligne, dates_facture[n_facture])


def test_provenance_tarification(generation: dict) -> None:
    entrees = generation["entrees"]
    lettres = entrees["nomenclature_lettres_cles"]["valeur"]

    assert len(lettres) == 7
    doc = [lettre for lettre in lettres if lettre["provenance"] == "DOC"]
    hyp = [lettre for lettre in lettres if lettre["provenance"] == "HYP"]

    assert len(doc) == 6, [lettre["code"] for lettre in doc]
    assert len(hyp) == 1, [lettre["code"] for lettre in hyp]
    assert hyp[0]["code"] == "J", hyp[0]
