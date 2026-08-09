"""Génère la table des passages depuis le fil des épisodes et les rendez-vous honorés.

Une ligne par épisode, exactement : le fil des épisodes n'est ni recompté ni refait ici,
seulement parcouru. Un passage issu d'une consultation programmée (catégorie C) porte
l'identifiant du rendez-vous honoré qui l'a programmé, retrouvé par appariement
patient-par-patient plutôt que par ordre d'apparition dans la table des rendez-vous — cet
ordre y est groupé par activité, pas par épisode. Ne tire aucun nombre en dehors du
générateur reçu en argument.
"""

import math
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np

from generator import config, ecriture, temporel

TABLE = "source.passages"

PILOTES = {
    "H": "admissions_annuelles",
    "C": "consultations_specialisees_externes",
    "U": "passages_urgences_par_jour",
}


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _profil_horaire_cache(
    jour: date, flux: str, entrees: dict[str, dict], cache: dict[tuple[date, str], list[float]]
) -> list[float]:
    # generator/temporel.py::tirer_horodatage ne reçoit pas les entrées déjà chargées et
    # recharge la configuration à chaque appel (calendrier.est_ferie, est_ramadan) : même
    # principe de mémorisation par jour que generator/rendez_vous.py::_CachesTemporelles,
    # sans réimplémenter aucune règle de calendrier.
    cle = (jour, flux)
    if cle not in cache:
        cache[cle] = temporel.profil_horaire_applicable(jour, flux, entrees)
    return cache[cle]


def _tirer_horodatage(
    jour: date,
    flux: str,
    entrees: dict[str, dict],
    cache: dict[tuple[date, str], list[float]],
    generateur: np.random.Generator,
) -> datetime:
    profil = _profil_horaire_cache(jour, flux, entrees, cache)
    heure = int(generateur.choice(24, p=profil))
    minute = int(generateur.integers(0, 60))
    seconde = int(generateur.integers(0, 60))
    return datetime(jour.year, jour.month, jour.day, heure, minute, seconde)


def _tirage_uniforme_liste(valeurs: list, generateur: np.random.Generator):
    return valeurs[int(generateur.integers(0, len(valeurs)))]


def _duree_minutes(
    mediane_minutes: float, ecart_type_log: float, generateur: np.random.Generator
) -> int:
    return max(1, int(round(generateur.lognormal(math.log(mediane_minutes), ecart_type_log))))


def _rendez_vous_honores_par_ipp(lignes_rendez_vous: list[dict]) -> dict[str, list[dict]]:
    par_ipp: dict[str, list[dict]] = defaultdict(list)
    for ligne in lignes_rendez_vous:
        if ligne["etat"] == "HO":
            par_ipp[ligne["n_ipp"]].append(ligne)
    for lignes in par_ipp.values():
        lignes.sort(key=lambda ligne: ligne["date_rendez_vous"])
    return par_ipp


def generer_lignes(
    episodes: list[dict],
    population: list[dict],
    lignes_rendez_vous: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> list[dict]:
    entrees = _entrees(entrees)

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    gabarit_ipp = entrees["gabarit_identifiant_patient"]["valeur"]
    correspondance_flux = entrees["correspondance_volume_flux"]["valeur"]
    correspondance_service = entrees["correspondance_type_passage_service"]["valeur"]
    correspondance_mode = entrees["correspondance_type_passage_mode_prise_en_charge"]["valeur"]
    duree_mediane_par_categorie = dict(entrees["duree_mediane_minutes_par_categorie"]["valeur"])
    duree_mediane_par_categorie["H"] = entrees["dms_publie"]["valeur"] * 24 * 60
    ecart_type_log_duree = entrees["ecart_type_log_duree"]["valeur"]
    ecart_type_avance_retard = entrees["ecart_type_minutes_avance_retard_rdv"]["valeur"]
    comptes = entrees["comptes_utilisateurs_passages"]["valeur"]
    noms_famille = entrees["noms_famille"]["valeur"]

    population_par_id = {p["patient_id"]: p for p in population}

    def n_ipp_pour(patient_id: int) -> str:
        return gabarit_ipp.format(rang=patient_id)

    honores_par_ipp = _rendez_vous_honores_par_ipp(lignes_rendez_vous)
    curseur_honores: dict[str, int] = defaultdict(int)

    cache_profil: dict[tuple[date, str], list[float]] = {}

    lignes: list[dict] = []
    rang_passage = 0

    def prochain_n_passage() -> str:
        nonlocal rang_passage
        rang_passage += 1
        return f"PSG-{rang_passage:07d}"

    for episode in episodes:
        categorie = episode["categorie"]
        patient_id = episode["patient_id"]
        n_ipp = n_ipp_pour(patient_id)
        jour = episode["date"]

        activite = None
        n_rdv = None

        if categorie == "C":
            idx = curseur_honores[n_ipp]
            ligne_rdv = honores_par_ipp[n_ipp][idx]
            curseur_honores[n_ipp] += 1

            activite = ligne_rdv["activite"]
            n_rdv = ligne_rdv["n_rdv"]

            offset_minutes = int(round(generateur.normal(0, ecart_type_avance_retard)))
            date_heure_entree = ligne_rdv["date_rendez_vous"] + timedelta(minutes=offset_minutes)
            date_creation_patient = population_par_id[patient_id]["date_creation"]
            if date_heure_entree.date() < date_creation_patient:
                date_heure_entree = ligne_rdv["date_rendez_vous"]
        else:
            flux = correspondance_flux[PILOTES[categorie]]
            date_heure_entree = _tirer_horodatage(jour, flux, entrees, cache_profil, generateur)

        mediane = duree_mediane_par_categorie[categorie]
        duree = _duree_minutes(mediane, ecart_type_log_duree, generateur)
        date_heure_sortie = date_heure_entree + timedelta(minutes=duree)
        if date_heure_sortie.date() > date_fin:
            date_heure_sortie = None

        ligne = {
            "n_passage": prochain_n_passage(),
            "n_ipp": n_ipp,
            "type_passage": categorie,
            "service": correspondance_service[categorie],
            "activite": activite,
            "n_rdv": n_rdv,
            "mode_prise_en_charge": correspondance_mode[categorie],
            "date_heure_entree": date_heure_entree,
            "date_heure_sortie": date_heure_sortie,
            "medecin": f"Dr. {_tirage_uniforme_liste(noms_famille, generateur)}",
            "cree_par": _tirage_uniforme_liste(comptes, generateur),
            "date_creation": date_heure_entree,
            "date_extraction": max(date_heure_entree.date(), date_debut),
        }
        lignes.append(ligne)

    return lignes


def ecrire_passages(
    racine,
    scenario: str,
    graine: int,
    episodes: list[dict],
    population: list[dict],
    lignes_rendez_vous: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> ecriture.Execution:
    entrees = _entrees(entrees)
    lignes = generer_lignes(episodes, population, lignes_rendez_vous, generateur, entrees=entrees)

    execution = ecriture.Execution(
        racine, scenario, graine, entrees["date_debut"]["valeur"], entrees["date_fin"]["valeur"]
    )
    execution.ecrire_table(TABLE, lignes)
    return execution
