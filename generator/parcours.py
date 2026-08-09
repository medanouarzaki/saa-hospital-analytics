"""Ordonne les épisodes de la période et leur attribue un patient.

Depuis les comptes journaliers de chaque catégorie d'épisode (produits par le module de
volumes, un compte par catégorie et par jour) et un générateur aléatoire reçu en argument,
produit la suite chronologique des épisodes et la population de patients qui les honore.
Ne tire aucun nombre en dehors du générateur reçu ; deux appels avec deux générateurs
construits depuis la même graine rendent le même résultat.

Conception du tirage pondéré retenue, mesurée avant d'être écrite (voir le rapport) :
la probabilité de retour d'un patient connu décroît exponentiellement avec le temps
écoulé depuis son dernier épisode ; le facteur de temps courant s'annulant à la
normalisation, un score non normalisé croissant avec la date du dernier épisode suffit.
Le tableau des scores cumulés n'est reconstruit qu'une fois par jour, pas une fois par
épisode ; le tirage lui-même se fait par recherche binaire dans ce tableau.
"""

import math
from datetime import date, timedelta

import numpy as np

from generator import config, temporel

FLUX_CONSULTATION = "programme"


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _tirage_pondere_dict(poids_par_code: dict[str, float], generateur: np.random.Generator) -> str:
    codes = list(poids_par_code.keys())
    poids = np.array([poids_par_code[c] for c in codes], dtype=float)
    poids = poids / poids.sum()
    return codes[int(generateur.choice(len(codes), p=poids))]


def _jour_ouvert_le_plus_proche_avant(
    jour: date, entrees: dict[str, dict], cache_poids: dict[date, float]
) -> date:
    # meme principe de memorisation que generator/rendez_vous.py::_CachesTemporelles :
    # generator/calendrier.py recharge la configuration a chaque appel (est_ferie,
    # est_ramadan), un cache par jour evite de le faire une fois par patient nouveau.
    candidat = jour
    while True:
        if candidat not in cache_poids:
            cache_poids[candidat] = temporel.poids_jour(candidat, FLUX_CONSULTATION, entrees)
        if cache_poids[candidat] > 0:
            return candidat
        candidat -= timedelta(days=1)


def _tirer_creation_fiche_consultation(
    jour_episode: date,
    entrees: dict[str, dict],
    generateur: np.random.Generator,
    cache_poids: dict[date, float],
) -> tuple[date, str]:
    # une fiche ouverte pour une premiere consultation programmee est creee au moment
    # de la prise de rendez-vous, pas le jour de la consultation elle-meme : reprend la
    # meme activite et le meme delai que ceux que generator/rendez_vous.py appliquerait
    # au rendez-vous honore correspondant, pour que les deux modules restent coherents
    # sans que l'un ne redecide ce que l'autre a deja fixe.
    activite = _tirage_pondere_dict(entrees["repartition_activites_rdv"]["valeur"], generateur)
    part_jour_meme = entrees["part_rdv_jour_meme"]["valeur"]
    if generateur.random() < part_jour_meme:
        delai = 0
    else:
        mediane = entrees["delai_rdv_par_specialite"]["valeur"][activite]
        ecart_type_log = entrees["ecart_type_log_delai"]["valeur"]
        delai = max(0, int(round(generateur.lognormal(math.log(mediane), ecart_type_log))))
    jour_prise = jour_episode - timedelta(days=delai)
    jour_prise = _jour_ouvert_le_plus_proche_avant(jour_prise, entrees, cache_poids)
    return jour_prise, activite


def construire_parcours(
    comptes_par_categorie: dict[str, dict[date, int]],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    entrees = _entrees(entrees)

    effectif_prealable = entrees["effectif_file_preexistante"]["valeur"]
    anciennete_max = entrees["anciennete_maximale_file_preexistante_jours"]["valeur"]
    part_connus = entrees["part_patients_connus"]["valeur"]
    echelle_jours = entrees["loi_decroissance_retour"]["valeur"]["echelle_jours"]
    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])

    population: list[dict] = []
    dernier_episode_jour: list[int] = []
    categorie_creation: list[str | None] = []

    if effectif_prealable > 0:
        decalages = generateur.integers(1, anciennete_max + 1, size=effectif_prealable)
        dates_creation_prealable = sorted(date_debut - timedelta(days=int(d)) for d in decalages)
        for date_creation in dates_creation_prealable:
            patient_id = len(population)
            population.append(
                {
                    "patient_id": patient_id,
                    "date_creation": date_creation,
                    "activite_creation": None,
                }
            )
            categorie_creation.append(None)
            dernier_episode_jour.append((date_creation - date_debut).days)

    categories = sorted(comptes_par_categorie.keys())
    tous_les_jours = sorted(
        set().union(*(set(comptes.keys()) for comptes in comptes_par_categorie.values()))
    )

    episodes: list[dict] = []
    poids_cumules = np.array([], dtype=float)

    for jour in tous_les_jours:
        offset_jour = (jour - date_debut).days

        if population:
            scores = np.exp(np.array(dernier_episode_jour, dtype=float) / echelle_jours)
            poids_cumules = np.cumsum(scores)

        for categorie in categories:
            n_episodes = comptes_par_categorie[categorie].get(jour, 0)
            for _ in range(n_episodes):
                connu = len(poids_cumules) > 0 and generateur.random() < part_connus

                if connu:
                    cible = generateur.random() * poids_cumules[-1]
                    indice = int(np.searchsorted(poids_cumules, cible, side="right"))
                    indice = min(indice, len(poids_cumules) - 1)
                    patient_id = population[indice]["patient_id"]
                else:
                    patient_id = len(population)
                    population.append(
                        {
                            "patient_id": patient_id,
                            "date_creation": jour,
                            "activite_creation": None,
                        }
                    )
                    categorie_creation.append(categorie)
                    dernier_episode_jour.append(offset_jour)

                dernier_episode_jour[patient_id] = offset_jour
                episodes.append({"date": jour, "categorie": categorie, "patient_id": patient_id})

    # deuxieme passe, une fois le fil des episodes entierement construit : deplace la
    # date de creation des fiches ouvertes par une premiere consultation programmee a
    # la date de prise du rendez-vous plutot qu'a la date de l'episode. Menee apres la
    # boucle principale pour ne consommer aucun tirage avant que toutes les decisions
    # connu/nouveau soient prises : le nombre d'episodes, leur repartition par
    # categorie, le nombre de patients distincts et l'ordre des identifiants restent
    # inchanges par cette deuxieme passe.
    cache_poids: dict[date, float] = {}
    for patient, categorie_patient in zip(population, categorie_creation, strict=True):
        if categorie_patient == "C":
            date_creation_fiche, activite = _tirer_creation_fiche_consultation(
                patient["date_creation"], entrees, generateur, cache_poids
            )
            patient["date_creation"] = date_creation_fiche
            patient["activite_creation"] = activite

    return episodes, population
