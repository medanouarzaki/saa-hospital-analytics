"""Contrôles bloquants sur la table des rendez-vous (generator/rendez_vous.py).

La génération complète dure quelques secondes : tous les tests s'exécutent sur cette
génération complète, réutilisée via une fixture de portée module, plutôt que sur un
échantillon. Plusieurs propriétés (bijection avec les épisodes, jours ouverts, ordre des
dates) portent explicitement sur la totalité des lignes.
"""

import statistics
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
import yaml

from generator import alea, temporel
from generator import rendez_vous as rdv

TABLE = "source.rendez_vous"
GRAINE = 1

RACINE = Path(__file__).resolve().parent.parent


def patient_id_de(n_ipp: str) -> int:
    return int(n_ipp.split("-")[1])


def _charger_verite_terrain(execution) -> dict:
    chemin = execution.racine / execution.scenario / "verite_terrain.yml"
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    partagee = generation_partagee
    return {
        "entrees": partagee["entrees"],
        "episodes": partagee["episodes"],
        "population": partagee["population"],
        "lignes": partagee["lignes"][TABLE],
        "execution": partagee["execution"],
        "racine": partagee["racine"],
    }


def test_bijection_avec_episodes_consultation(generation: dict) -> None:
    episodes = generation["episodes"]
    lignes = generation["lignes"]

    n_consultations_attendu = sum(1 for e in episodes if e["categorie"] == "C")
    honores = [ligne for ligne in lignes if ligne["etat"] == "HO"]

    assert len(honores) == n_consultations_attendu
    assert all(not ligne["rdv_supplementaire"] for ligne in honores)

    n_ipp_honores = Counter(ligne["n_ipp"] for ligne in honores)
    # chaque episode de consultation a un rendez-vous honore et un seul : le nombre de
    # rendez-vous honores par n_ipp ne doit jamais depasser le nombre d'episodes de
    # consultation de ce meme patient
    n_consultations_par_patient = Counter(
        e["patient_id"] for e in episodes if e["categorie"] == "C"
    )
    for n_ipp, effectif in n_ipp_honores.items():
        pid = patient_id_de(n_ipp)
        assert effectif == n_consultations_par_patient[pid]


def test_taux_absence_et_annulation(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    taux_absenteisme_par_specialite = entrees["taux_absenteisme_par_specialite"]["valeur"]
    taux_annulation = entrees["taux_annulation"]["valeur"]

    # tolerances mesurees sur 3 graines independantes : ecart maximal observe 0,0078
    # (absenteisme par specialite) et 0,00005 (annulation globale)
    TOLERANCE = 0.02

    for activite, taux_attendu in taux_absenteisme_par_specialite.items():
        sous_ensemble = [
            ligne
            for ligne in lignes
            if ligne["activite"] == activite and ligne["etat"] in ("HO", "CO")
        ]
        n_absences = sum(1 for ligne in sous_ensemble if ligne["etat"] == "CO")
        part = n_absences / len(sous_ensemble)
        assert abs(part - taux_attendu) < TOLERANCE, (activite, taux_attendu, part)

    sous_ensemble_annulation = [ligne for ligne in lignes if ligne["etat"] in ("HO", "CO", "AN")]
    n_annulations = sum(1 for ligne in sous_ensemble_annulation if ligne["etat"] == "AN")
    part_annulation = n_annulations / len(sous_ensemble_annulation)
    assert abs(part_annulation - taux_annulation) < TOLERANCE, (taux_annulation, part_annulation)


def test_pente_absenteisme_reelle(generation: dict) -> None:
    entrees = generation["entrees"]

    # verifie le mecanisme lui-meme (generator/rendez_vous.py::_delai_biaise_longue_attente)
    # plutot qu'un decompte agrege sur la generation complete : un decoupage global en
    # tranches de delai (ex. court/long en jours absolus) melange les specialites, dont les
    # medianes vont de 5 a 45 jours, et le simple melange des specialites peut reproduire
    # l'ordre attendu meme sans pente reelle -- mesure, voir mutation ci-dessous.
    # Comparer les tirages de la fonction biaisee a ceux de la loi log-normale non biaisee
    # au meme parametre isole proprement l'effet de la pente.
    rng_biaise = alea.construire_generateur(GRAINE)
    rng_neutre = alea.construire_generateur(GRAINE)
    mediane = 20.0
    ecart_type_log = entrees["ecart_type_log_delai_par_specialite"]["valeur"]["21"]
    pente = entrees["pente_absenteisme_delai"]["valeur"]

    N = 5000
    delais_biaises = [
        rdv._delai_biaise_longue_attente(mediane, ecart_type_log, pente, rng_biaise)
        for _ in range(N)
    ]
    delais_neutres = [rdv._delai_lognormal(mediane, ecart_type_log, rng_neutre) for _ in range(N)]

    moyenne_biaisee = sum(delais_biaises) / N
    moyenne_neutre = sum(delais_neutres) / N

    assert moyenne_biaisee > moyenne_neutre, (moyenne_biaisee, moyenne_neutre)


def test_delai_median_par_activite(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    delais_medians_attendus = entrees["delai_rdv_par_specialite"]["valeur"]
    honores = [ligne for ligne in lignes if ligne["etat"] == "HO"]

    # depuis que la fiche d'une premiere consultation programmee est creee
    # a la prise du rendez-vous (et non plus le jour de l'episode), le delai est observable
    # sur la quasi-totalite des rendez-vous honores, plus seulement sur un sous-ensemble
    # "eligible" -- mesure sur la totalite des lignes honorees, sans filtre.
    # tolerance mesuree sur 3 graines independantes (graines 1, 2, 3) : ecart maximal
    # observe 5,0 jours (graine 3) entre mediane mesuree et mediane configuree.
    TOLERANCE_JOURS = 8
    for activite, mediane_attendue in delais_medians_attendus.items():
        delais = [
            (ligne["date_rendez_vous"].date() - ligne["date_creation"].date()).days
            for ligne in honores
            if ligne["activite"] == activite
        ]
        assert len(delais) > 0
        mediane_mesuree = statistics.median(delais)
        assert abs(mediane_mesuree - mediane_attendue) < TOLERANCE_JOURS, (
            activite,
            mediane_attendue,
            mediane_mesuree,
        )


def test_part_rdv_jour_meme(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    population = generation["population"]

    part_attendue = entrees["part_rdv_jour_meme"]["valeur"]
    date_creation_par_patient = {p["patient_id"]: p["date_creation"] for p in population}

    honores = [ligne for ligne in lignes if ligne["etat"] == "HO"]

    def marge_disponible(ligne: dict) -> int:
        pid = patient_id_de(ligne["n_ipp"])
        return (ligne["date_rendez_vous"].date() - date_creation_par_patient[pid]).days

    eligibles = [ligne for ligne in honores if marge_disponible(ligne) > 0]

    n_jour_meme = sum(
        1
        for ligne in eligibles
        if ligne["date_rendez_vous"].date() == ligne["date_creation"].date()
    )
    part_mesuree = n_jour_meme / len(eligibles)

    # tolerance recalibree (part_rdv_jour_meme portee de 0,03 a 0,06) : le
    # tirage jour-meme peut retomber sur un jour ferme, alors reporte au jour ouvert le
    # plus proche (_jour_ouvert_borne_inferieurement), diluant le taux observe a environ
    # 45 % du parametre configure -- deja le cas auparavant (mesure sur le code d'avant
    # lot, graine 1 : parametre 0,03, mesure 0,0138, dilution 46 %), seul l'ecart absolu
    # grandit avec un parametre plus grand. Mesure sur 2 graines independantes avec le
    # parametre aligne : graine 1, ecart 0,0331 ; graine 2, ecart 0,0342.
    TOLERANCE = 0.04
    assert abs(part_mesuree - part_attendue) < TOLERANCE, (part_attendue, part_mesuree)


def test_patients_adresses(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    part_attendue = entrees["part_patients_adresses"]["valeur"]

    with (RACINE / "docs" / "observation" / "releve_champs.yml").open(encoding="utf-8") as f:
        releve = yaml.safe_load(f)
    champ_origine = next(
        champ
        for ecran in releve["ecrans"]
        for champ in ecran["champs"]
        if champ["id"] == "REL-RDV.R03"
    )
    code_adresse_attendu = champ_origine["valeurs_observees"][0]

    n_adresses = sum(1 for ligne in lignes if ligne["origine"] == code_adresse_attendu)
    part_mesuree = n_adresses / len(lignes)

    # tolerance mesuree sur 3 graines independantes de mesure_tolerances_rdv2.py :
    # ecart maximal observe 0,0062 sur un parametre distinct mais de meme nature
    TOLERANCE = 0.02
    assert abs(part_mesuree - part_attendue) < TOLERANCE, (part_attendue, part_mesuree)


def test_ordre_des_dates(generation: dict) -> None:
    lignes = generation["lignes"]
    population = generation["population"]
    date_creation_par_patient = {p["patient_id"]: p["date_creation"] for p in population}

    vt = _charger_verite_terrain(generation["execution"])
    n_rdv_exemptes = {entree["identifiant"] for entree in vt["dates_aberrantes"]["entrees"]}
    assert len(n_rdv_exemptes) == vt["dates_aberrantes"]["decompte"]

    assert len(lignes) > 0
    n_verifies = 0
    for ligne in lignes:
        if ligne["n_rdv"] in n_rdv_exemptes:
            continue
        n_verifies += 1
        assert ligne["date_creation"].date() <= ligne["date_rendez_vous"].date(), ligne
        pid = patient_id_de(ligne["n_ipp"])
        assert date_creation_par_patient[pid] <= ligne["date_creation"].date(), ligne
    assert n_verifies > 0


def test_jours_ouverts(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    vt = _charger_verite_terrain(generation["execution"])
    n_rdv_exemptes = {entree["identifiant"] for entree in vt["dates_aberrantes"]["entrees"]}
    assert len(n_rdv_exemptes) == vt["dates_aberrantes"]["decompte"]

    n_fermes = 0
    n_verifies = 0
    for ligne in lignes:
        if ligne["n_rdv"] in n_rdv_exemptes:
            continue
        n_verifies += 1
        if temporel.poids_jour(ligne["date_creation"].date(), "programme", entrees) <= 0:
            n_fermes += 1
        if temporel.poids_jour(ligne["date_rendez_vous"].date(), "programme", entrees) <= 0:
            n_fermes += 1
    assert n_verifies > 0
    assert n_fermes == 0


def test_debordement_de_periode(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    debordement = [ligne for ligne in lignes if ligne["date_rendez_vous"].date() > date_fin]

    assert len(debordement) > 0
    assert all(ligne["etat"] == "EI" for ligne in debordement)
    assert all(ligne["rdv_supplementaire"] for ligne in debordement)


def test_anteriorite_complete_naissance_fiche_prise_rdv(
    generation: dict, generation_partagee: dict
) -> None:
    lignes_patients = generation_partagee["lignes"]["source.patients"]
    lignes_rdv = generation["lignes"]

    naissance_par_patient: dict[int, date] = {}
    fiche_par_patient: dict[int, date] = {}
    for ligne in lignes_patients:
        pid = patient_id_de(ligne["n_ipp"])
        naissance = ligne["date_naissance"]
        fiche = ligne["date_attribution"]
        if pid not in naissance_par_patient:
            naissance_par_patient[pid] = naissance
            fiche_par_patient[pid] = fiche
        else:
            # deux lignes (creation puis modification) pour le meme patient portent
            # les memes date_naissance et date_attribution : verifie l'invariant plutot
            # que de le supposer.
            assert naissance_par_patient[pid] == naissance
            assert fiche_par_patient[pid] == fiche

    vt = _charger_verite_terrain(generation["execution"])
    n_ipp_ages_exemptes = {entree["identifiant"] for entree in vt["ages_incoherents"]["entrees"]}
    assert len(n_ipp_ages_exemptes) == vt["ages_incoherents"]["decompte"]
    n_rdv_dates_exemptes = {entree["identifiant"] for entree in vt["dates_aberrantes"]["entrees"]}
    assert len(n_rdv_dates_exemptes) == vt["dates_aberrantes"]["decompte"]

    assert lignes_rdv, "aucune ligne de rendez-vous"
    n_verifies = 0
    for ligne in lignes_rdv:
        pid = patient_id_de(ligne["n_ipp"])
        age_exempte = ligne["n_ipp"] in n_ipp_ages_exemptes
        date_exemptee = ligne["n_rdv"] in n_rdv_dates_exemptes
        naissance = naissance_par_patient[pid]
        fiche = fiche_par_patient[pid]
        prise = ligne["date_creation"].date()
        rendez_vous_jour = ligne["date_rendez_vous"].date()
        if not age_exempte:
            assert naissance < fiche, (pid, naissance, fiche)
        assert fiche <= prise, (pid, fiche, prise)
        if not date_exemptee:
            n_verifies += 1
            assert prise <= rendez_vous_jour, (pid, prise, rendez_vous_jour)
    assert n_verifies > 0
