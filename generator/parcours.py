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

from datetime import date, timedelta

import numpy as np

from generator import config


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


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

    if effectif_prealable > 0:
        decalages = generateur.integers(1, anciennete_max + 1, size=effectif_prealable)
        dates_creation_prealable = sorted(date_debut - timedelta(days=int(d)) for d in decalages)
        for date_creation in dates_creation_prealable:
            patient_id = len(population)
            population.append({"patient_id": patient_id, "date_creation": date_creation})
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
                    population.append({"patient_id": patient_id, "date_creation": jour})
                    dernier_episode_jour.append(offset_jour)

                dernier_episode_jour[patient_id] = offset_jour
                episodes.append({"date": jour, "categorie": categorie, "patient_id": patient_id})

    return episodes, population
