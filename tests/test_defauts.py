"""Contrôles bloquants sur l'injection des défauts de surface (generator/defauts.py) et sur
le fichier de vérité terrain complet qu'elle produit (generator/verite_terrain.py).
"""

import csv
import subprocess
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
import yaml

from generator import config, defauts, ecriture, execution, nomenclatures, patients, registre

GRAINE_PARTAGEE = 1
TOLERANCE_TAUX = 0.002

TABLE_PAT = "source.patients"
TABLE_RDV = "source.rendez_vous"
TABLE_FAC = "source.factures"
TABLE_PEC = "source.prises_en_charge"
TABLE_PAS = "source.passages"


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def _charger_verite_terrain(execution_obj: ecriture.Execution) -> dict:
    chemin = execution_obj.racine / execution_obj.scenario / "verite_terrain.yml"
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fiches(lignes_patients: list[dict]) -> dict[str, dict]:
    fiches: dict[str, dict] = {}
    for ligne in lignes_patients:
        fiches.setdefault(ligne["n_ipp"], ligne)
    return fiches


def test_taux_mesures(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    fiches = _fiches(lignes[TABLE_PAT])
    n_fiches = len(fiches)

    taux_champs_manquants = entrees["taux_champs_manquants"]["valeur"]
    for colonne, taux in taux_champs_manquants.items():
        n_manquant = sum(1 for f in fiches.values() if f[colonne] is None)
        part = n_manquant / n_fiches
        assert abs(part - taux) < TOLERANCE_TAUX, (colonne, taux, part)

    lignes_rdv = lignes[TABLE_RDV]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    doublons_creneau = [
        ligne
        for ligne in lignes_rdv
        if ligne["etat"] == "EI" and ligne["date_rendez_vous"].date() <= date_fin
    ]
    # denominateur identique a celui de generator/defauts.py::_injecter_rdv_doublon_creneau :
    # les rendez-vous honores, hors ceux deja touches par une date aberrante (jamais
    # eligibles a la duplication).
    n_honores_eligibles = sum(
        1
        for ligne in lignes_rdv
        if ligne["etat"] == "HO" and ligne["date_rendez_vous"] != defauts.DATE_ABERRANTE
    )
    taux_rdv = entrees["taux_rdv_doublon_creneau"]["valeur"]
    part_rdv = len(doublons_creneau) / n_honores_eligibles
    assert abs(part_rdv - taux_rdv) < TOLERANCE_TAUX, (taux_rdv, part_rdv)

    taux_dates = entrees["taux_dates_aberrantes"]["valeur"]
    n_dates_aberrantes = sum(
        1 for ligne in lignes_rdv if ligne["date_rendez_vous"] == defauts.DATE_ABERRANTE
    )
    part_dates = n_dates_aberrantes / len(lignes_rdv)
    assert abs(part_dates - taux_dates) < TOLERANCE_TAUX, (taux_dates, part_dates)

    # les trois categories de defaut de surface sont mutuellement exclusives (pools de
    # selection disjoints, generator/defauts.py::_injecter_defauts_surface) et detectables
    # par motif sur la valeur seule, sans les originaux : le pool de voies
    # (pool_foyers.voies) ne porte aucun accent et une casse Titre constante, donc seule
    # une adresse entierement en minuscules ou entierement en majuscules peut provenir d'une
    # alteration -- controle positif d'abord, sur une valeur fabriquee.
    assert "avenue hassan ii".islower() and not "avenue hassan ii".isupper()
    assert "AVENUE HASSAN II".isupper() and not "AVENUE HASSAN II".islower()
    taux_surface = entrees["taux_defauts_surface"]["valeur"]
    adresses = [f["adresse"] for f in fiches.values()]
    n_majuscules = sum(1 for a in adresses if a.isupper())
    n_minuscules = sum(1 for a in adresses if a.islower())
    n_espaces_multiples = sum(1 for a in adresses if "  " in a)
    for categorie, n_observe in (
        ("majuscules", n_majuscules),
        ("casse_accents", n_minuscules),
        ("espaces_multiples", n_espaces_multiples),
    ):
        part = n_observe / n_fiches
        assert abs(part - taux_surface[categorie]) < TOLERANCE_TAUX, (
            categorie,
            taux_surface[categorie],
            part,
        )

    taux_ages = entrees["taux_ages_incoherents"]["valeur"]
    n_ages_incoherents = sum(
        1
        for f in fiches.values()
        if f["date_naissance"] >= f["date_attribution"]
        or (f["date_attribution"] - f["date_naissance"]).days > 120 * 365
    )
    part_ages = n_ages_incoherents / n_fiches
    assert abs(part_ages - taux_ages) < TOLERANCE_TAUX, (taux_ages, part_ages)


def test_exactitude_verite_terrain_biunivoque(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    fiches = _fiches(lignes[TABLE_PAT])
    vt = _charger_verite_terrain(generation["execution"])

    # sens 1 : chaque entree du fichier correspond a une valeur actuellement observee
    for categorie in (
        "champs_manquants",
        "defauts_surface",
        "dates_aberrantes",
        "ages_incoherents",
        "factures_sans_pec",
    ):
        assert vt[categorie]["decompte"] == len(vt[categorie]["entrees"])

    for entree in vt["champs_manquants"]["entrees"]:
        assert fiches[entree["identifiant"]][entree["colonne"]] is None, entree

    for entree in vt["ages_incoherents"]["entrees"]:
        f = fiches[entree["identifiant"]]
        assert f["date_naissance"] == entree["apres"], entree

    lignes_rdv_par_id = {ligne["n_rdv"]: ligne for ligne in lignes[TABLE_RDV]}
    for entree in vt["dates_aberrantes"]["entrees"]:
        assert lignes_rdv_par_id[entree["identifiant"]]["date_rendez_vous"] == entree["apres"]

    for entree in vt["rdv_doublon_creneau"]["entrees"]:
        assert entree["identifiant"] in lignes_rdv_par_id
        assert lignes_rdv_par_id[entree["identifiant"]]["etat"] == "EI"

    n_episodes_avec_pec = {pec["n_episode"] for pec in lignes[TABLE_PEC]}
    for entree in vt["factures_sans_pec"]["entrees"]:
        facture = next(f for f in lignes[TABLE_FAC] if f["n_facture"] == entree["identifiant"])
        assert facture["n_episode"] not in n_episodes_avec_pec, entree
        assert facture["part_organisme"] == 0.0, entree
        assert facture["part_patient"] == pytest.approx(facture["montant_total"]), entree

    # sens 2 : la somme structurel + injecte egale le total observe (champs manquants),
    # et le decompte des categories a marqueur reconnaissable egale le total independant
    # (dates aberrantes, ages incoherents) -- verifie a nouveau ici independamment de
    # test_taux_mesures, sur le decompte de la verite terrain plutot que sur le taux.
    taux_champs_manquants = entrees["taux_champs_manquants"]["valeur"]
    decompte_structurel = Counter(e["colonne"] for e in vt["absence_structurelle"]["entrees"])
    decompte_injecte = Counter(e["colonne"] for e in vt["champs_manquants"]["entrees"])
    for colonne in taux_champs_manquants:
        n_manquant_observe = sum(1 for f in fiches.values() if f[colonne] is None)
        assert decompte_structurel[colonne] + decompte_injecte[colonne] == n_manquant_observe

    n_dates_aberrantes_observe = sum(
        1 for ligne in lignes[TABLE_RDV] if ligne["date_rendez_vous"] == defauts.DATE_ABERRANTE
    )
    assert vt["dates_aberrantes"]["decompte"] == n_dates_aberrantes_observe

    n_ages_incoherents_observe = sum(
        1
        for f in fiches.values()
        if f["date_naissance"] >= f["date_attribution"]
        or (f["date_attribution"] - f["date_naissance"]).days > 120 * 365
    )
    assert vt["ages_incoherents"]["decompte"] == n_ages_incoherents_observe

    adresses = [f["adresse"] for f in fiches.values()]
    decompte_surface_observe = {
        "majuscules": sum(1 for a in adresses if a.isupper()),
        "casse_accents": sum(1 for a in adresses if a.islower()),
        "espaces_multiples": sum(1 for a in adresses if "  " in a),
    }
    decompte_surface_vt = Counter(e["categorie_surface"] for e in vt["defauts_surface"]["entrees"])
    for categorie, n_observe in decompte_surface_observe.items():
        assert decompte_surface_vt[categorie] == n_observe, categorie

    # date_facture ancre l'evenement : la couverture applicable a une facture est celle en
    # vigueur a sa date, pas la derniere version reextraite du patient (mesure et corrige au
    # lot qui a introduit le changement metier sur compagnie_assurance, voir le rapport).
    versions_par_ipp_pat: dict[str, list[dict]] = {}
    for ligne in lignes[TABLE_PAT]:
        versions_par_ipp_pat.setdefault(ligne["n_ipp"], []).append(ligne)

    def compagnie_en_vigueur(n_ipp: str, jour) -> str:
        versions_triees = sorted(versions_par_ipp_pat[n_ipp], key=lambda v: v["date_extraction"])
        candidates = [v for v in versions_triees if v["date_extraction"] <= jour]
        version = candidates[-1] if candidates else versions_triees[0]
        return version["compagnie_assurance"]

    # anti-vacuite : au moins une facture doit voir une couverture differente selon qu'on
    # prenne la derniere version reextraite ou la version en vigueur a sa date -- sans quoi
    # le controle de taux ci-dessous ne distinguerait pas les deux semantiques.
    n_cas_discriminants = 0
    for f in lignes[TABLE_FAC]:
        versions_ipp = versions_par_ipp_pat.get(f["n_ipp"])
        if versions_ipp is None or len(versions_ipp) != 2:
            continue
        derniere = max(versions_ipp, key=lambda v: v["date_extraction"])
        if (derniere["compagnie_assurance"] != "SANS") != (
            compagnie_en_vigueur(f["n_ipp"], f["date_facture"]) != "SANS"
        ):
            n_cas_discriminants += 1
    assert n_cas_discriminants > 0, "aucun cas discriminant : le test serait vrai par vacuité"

    n_couvertes = sum(
        1
        for f in lignes[TABLE_FAC]
        if compagnie_en_vigueur(f["n_ipp"], f["date_facture"]) != "SANS"
    )
    n_sans_pec_observe = sum(
        1
        for f in lignes[TABLE_FAC]
        if compagnie_en_vigueur(f["n_ipp"], f["date_facture"]) != "SANS"
        and f["n_episode"] not in n_episodes_avec_pec
    )
    taux_factures_sans_pec = entrees["taux_factures_sans_pec"]["valeur"]
    assert abs(n_sans_pec_observe / n_couvertes - taux_factures_sans_pec) < TOLERANCE_TAUX


def _lignes_patients_csv(execution_obj: ecriture.Execution) -> list[dict]:
    lignes: list[dict] = []
    for relatif in execution_obj.partitions[TABLE_PAT]:
        if not relatif.endswith(".csv"):
            continue
        with (execution_obj.racine / relatif).open(encoding="utf-8") as f:
            lignes.extend(csv.DictReader(f))
    return lignes


def _versions_multiples(execution_obj: ecriture.Execution) -> dict[str, tuple[dict, dict]]:
    """Regroupe les lignes patients par n_ipp, ne retenant que les n_ipp à exactement deux
    versions, ordonnées (création, modification) via la présence de `date_modification` --
    indépendamment de `generator/verite_terrain.py::_calculer_fiches_modifiees`, pour que ce
    test vérifie la propriété elle-même plutôt que la logique de production qui la calcule."""
    par_ipp: dict[str, list[dict]] = {}
    for ligne in _lignes_patients_csv(execution_obj):
        par_ipp.setdefault(ligne["n_ipp"], []).append(ligne)
    resultat = {}
    for n_ipp, versions in par_ipp.items():
        if len(versions) != 2:
            continue
        creation, modification = sorted(
            versions, key=lambda v: v["date_modification"] == "", reverse=True
        )
        resultat[n_ipp] = (creation, modification)
    return resultat


def test_fiches_modifiees_exactement_enregistrees(generation: dict) -> None:
    """Le changement métier est réel et exactement enregistré. Égalité d'ensembles dans les
    deux sens (pas d'échantillon) : chaque entrée de `fiches_modifiees` correspond à une
    différence réelle sur disque, et tout n_ipp multi-version absent de la catégorie ne porte
    aucune différence métier réelle."""
    execution_obj = generation["execution"]
    vt = _charger_verite_terrain(execution_obj)

    colonnes_comparees = [
        c
        for c in registre.colonnes_table(TABLE_PAT)
        if c not in {"n_ipp", "date_extraction", "date_modification", "modifie_par"}
    ]

    versions = _versions_multiples(execution_obj)
    entrees_vt = {e["n_ipp"]: e for e in vt["fiches_modifiees"]["entrees"]}
    # non-vacuite : sur la generation partagee, des changements metier reels doivent
    # exister, sans quoi les deux boucles ci-dessous seraient vides et l'egalite
    # d'ensembles se verifierait trivialement sans rien prouver (regle de mutation).
    assert vt["fiches_modifiees"]["decompte"] > 0
    assert any(diff for diff in entrees_vt.values())
    assert vt["fiches_modifiees"]["decompte"] == len(vt["fiches_modifiees"]["entrees"])
    assert set(entrees_vt) <= set(versions), "une entrée de fiches_modifiees sans deux versions"

    for n_ipp, (creation, modification) in versions.items():
        diff_reel = {
            colonne: (creation[colonne], modification[colonne])
            for colonne in colonnes_comparees
            if creation[colonne] != modification[colonne]
        }
        if n_ipp in entrees_vt:
            colonnes_vt = entrees_vt[n_ipp]["colonnes"]
            assert set(colonnes_vt) == set(diff_reel), n_ipp
            for colonne, valeurs in colonnes_vt.items():
                assert valeurs["avant"] == diff_reel[colonne][0], (n_ipp, colonne)
                assert valeurs["apres"] == diff_reel[colonne][1], (n_ipp, colonne)
        else:
            assert diff_reel == {}, (n_ipp, "difference metier non enregistree")


def test_fiches_modifiees_colonnes_du_type(generation: dict) -> None:
    """Chaque entrée de `fiches_modifiees` ne porte que des colonnes autorisées pour son
    `type_modification`, vérifié contre la définition partagée
    `generator.patients.COLONNES_PAR_TYPE_MODIFICATION` (mapping unique : ni la production ni
    ce test ne maintiennent une copie séparée de cette liste)."""
    vt = _charger_verite_terrain(generation["execution"])
    assert vt["fiches_modifiees"]["decompte"] > 0
    for entree in vt["fiches_modifiees"]["entrees"]:
        colonnes_autorisees = set(
            patients.COLONNES_PAR_TYPE_MODIFICATION[entree["type_modification"]]
        )
        assert set(entree["colonnes"]) <= colonnes_autorisees, entree
        assert set(entree["colonnes"]), entree


def test_aucune_colonne_codee_alteree(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    correspondance = entrees["correspondance_colonnes_nomenclatures"]["valeur"]

    n_colonnes_verifiees = 0
    for table in execution.tables_couvertes():
        lignes_table = lignes[table]
        colonnes_codees = [c for c in correspondance if c["table"] == table]
        for correspondance_colonne in colonnes_codees:
            colonne = correspondance_colonne["colonne"]
            nom_nomenclature = nomenclatures.nomenclature_colonne(table, colonne, entrees)
            codes_valides = set(nomenclatures.codes_nomenclature(nom_nomenclature, entrees))
            valeurs_observees = {
                ligne[colonne] for ligne in lignes_table if ligne[colonne] is not None
            }
            n_colonnes_verifiees += 1
            assert valeurs_observees <= codes_valides, (
                table,
                colonne,
                valeurs_observees - codes_valides,
            )
    assert n_colonnes_verifiees > 0


def test_aucune_jointure_rompue(generation: dict) -> None:
    lignes = generation["lignes"]

    lignes_rdv = lignes[TABLE_RDV]
    n_rdv_tous = [ligne["n_rdv"] for ligne in lignes_rdv]
    assert len(n_rdv_tous) == len(set(n_rdv_tous)), "identifiant de rendez-vous en double"

    n_ipp_patients = {p["n_ipp"] for p in lignes[TABLE_PAT]}
    assert all(ligne["n_ipp"] in n_ipp_patients for ligne in lignes_rdv)

    n_rdv_honores = {ligne["n_rdv"] for ligne in lignes_rdv if ligne["etat"] == "HO"}
    passages_rattaches = [p for p in lignes[TABLE_PAS] if p["n_rdv"] is not None]
    assert all(p["n_rdv"] in n_rdv_honores for p in passages_rattaches)
    assert {p["n_rdv"] for p in passages_rattaches} == n_rdv_honores

    n_episode_factures = {f["n_episode"] for f in lignes[TABLE_FAC]}
    assert all(pec["n_episode"] in n_episode_factures for pec in lignes[TABLE_PEC])
    n_episode_pec = [pec["n_episode"] for pec in lignes[TABLE_PEC]]
    assert len(n_episode_pec) == len(set(n_episode_pec)), "prise en charge en double"


def test_absence_structurelle_et_alteration_distinctes(generation: dict) -> None:
    vt = _charger_verite_terrain(generation["execution"])
    cles_structurelles = {
        (e["table"], e["colonne"], e["identifiant"]) for e in vt["absence_structurelle"]["entrees"]
    }
    cles_alterees = {
        (e["table"], e["colonne"], e["identifiant"]) for e in vt["champs_manquants"]["entrees"]
    }
    assert cles_structurelles, "aucune absence structurelle a controler"
    assert cles_alterees, "aucune alteration a controler"
    assert cles_structurelles.isdisjoint(cles_alterees)


def test_bijection_preservee_malgre_doublons_creneau(generation: dict) -> None:
    episodes = generation["episodes"]
    lignes_rdv = generation["lignes"][TABLE_RDV]

    vt = _charger_verite_terrain(generation["execution"])
    assert vt["rdv_doublon_creneau"]["decompte"] > 0

    n_consultations_attendu = sum(1 for e in episodes if e["categorie"] == "C")
    honores = [ligne for ligne in lignes_rdv if ligne["etat"] == "HO"]
    assert len(honores) == n_consultations_attendu


def test_reproductibilite_deux_graines(tmp_path_factory) -> None:
    entrees = {e["nom"]: e for e in config.charger_entrees()}
    racine_a1 = tmp_path_factory.mktemp("defauts_repro_a1")
    racine_a2 = tmp_path_factory.mktemp("defauts_repro_a2")
    racine_b = tmp_path_factory.mktemp("defauts_repro_b")

    execution_a1, _ = execution.executer(racine_a1, GRAINE_PARTAGEE, entrees=entrees)
    execution_a2, _ = execution.executer(racine_a2, GRAINE_PARTAGEE, entrees=entrees)
    execution_b, _ = execution.executer(racine_b, GRAINE_PARTAGEE + 1, entrees=entrees)

    vt_a1 = _charger_verite_terrain(execution_a1)
    vt_a2 = _charger_verite_terrain(execution_a2)
    vt_b = _charger_verite_terrain(execution_b)

    for categorie in (
        "champs_manquants",
        "defauts_surface",
        "dates_aberrantes",
        "ages_incoherents",
        "rdv_doublon_creneau",
        "factures_sans_pec",
    ):
        assert vt_a1[categorie]["entrees"] == vt_a2[categorie]["entrees"], categorie
        # controle positif : une graine differente doit produire des alterations differentes
        assert vt_a1[categorie]["entrees"] != vt_b[categorie]["entrees"], categorie

    empreintes_a1 = {k: v for k, v in execution_a1.empreintes.items() if k.endswith(".csv")}
    empreintes_a2 = {k: v for k, v in execution_a2.empreintes.items() if k.endswith(".csv")}
    assert empreintes_a1 == empreintes_a2


def test_verite_terrain_hors_du_traitement() -> None:
    racine = Path(__file__).resolve().parent.parent
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        contenu_original = (racine / "generator" / "urgences.py").read_text(encoding="utf-8")
        f.write(contenu_original + "\nfrom generator import verite_terrain  # controle positif\n")
        chemin_positif = Path(f.name)
    try:
        positif = subprocess.run(
            ["grep", "-c", "verite_terrain", str(chemin_positif)],
            capture_output=True,
            text=True,
        )
        assert positif.returncode == 0 and int(positif.stdout.strip()) >= 1

        reel = subprocess.run(
            [
                "grep",
                "-rl",
                "verite_terrain",
                str(racine / "generator"),
                "--include=*.py",
            ],
            capture_output=True,
            text=True,
        )
        fichiers_trouves = {Path(p).name for p in reel.stdout.strip().splitlines() if p}
        assert fichiers_trouves <= {"execution.py", "verite_terrain.py"}
    finally:
        chemin_positif.unlink()
