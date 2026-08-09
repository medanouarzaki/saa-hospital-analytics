"""Moteur de modulation temporelle, lu depuis generator/config/temporel.yml.

Ne porte aucune valeur en dur : tout vient de la configuration et du module
de calendrier. Ne connaît ni tables, ni colonnes, ni volumes cibles.
"""

from datetime import date, datetime

import numpy as np

from generator import calendrier, config


def _entrees() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def poids_jour(jour: date, flux: str, entrees: dict[str, dict] | None = None) -> float:
    if entrees is None:
        entrees = _entrees()

    facteur_semaine = entrees["profil_hebdomadaire"]["valeur"][flux][jour.weekday()]

    calendaire = entrees["effet_calendaire"]["valeur"]
    facteur_ferie = calendaire[f"coefficient_ferie_{flux}"] if calendrier.est_ferie(jour) else 1.0
    facteur_aout = calendaire[f"coefficient_aout_{flux}"] if jour.month == 8 else 1.0

    ramadan = entrees["effet_ramadan"]["valeur"]
    facteur_ramadan = ramadan[f"coefficient_{flux}"] if calendrier.est_ramadan(jour) else 1.0

    return facteur_semaine * facteur_ferie * facteur_aout * facteur_ramadan


def repartir_total(total: int, jours: list[date], flux: str) -> dict[date, int]:
    entrees = _entrees()
    poids = {jour: poids_jour(jour, flux, entrees) for jour in jours}
    somme_poids = sum(poids.values())

    if somme_poids == 0 or total == 0:
        return {jour: 0 for jour in jours}

    bruts = {jour: total * p / somme_poids for jour, p in poids.items()}
    entiers = {jour: int(b) for jour, b in bruts.items()}
    reste = total - sum(entiers.values())

    candidats = sorted(
        (jour for jour in jours if poids[jour] > 0),
        key=lambda jour: bruts[jour] - entiers[jour],
        reverse=True,
    )
    for jour in candidats[:reste]:
        entiers[jour] += 1

    return entiers


def profil_horaire_applicable(
    jour: date, flux: str, entrees: dict[str, dict] | None = None
) -> list[float]:
    if entrees is None:
        entrees = _entrees()

    base = list(entrees["profil_horaire"]["valeur"][flux])

    if flux == "programme" and calendrier.est_ramadan(jour):
        decalage = entrees["effet_ramadan"]["valeur"]["decalage_heures_programme"]
        base = [base[(heure - decalage) % 24] for heure in range(24)]

    if flux == "urgences" and calendrier.est_ramadan(jour):
        ramadan = entrees["effet_ramadan"]["valeur"]
        heure_rupture = ramadan["heure_rupture_jeune"]
        duree = ramadan["duree_report_heures"]
        intensite = ramadan["intensite_report_urgences"]
        heures_fenetre = {(heure_rupture + decalage) % 24 for decalage in range(duree)}
        base = [
            valeur * intensite if heure in heures_fenetre else valeur
            for heure, valeur in enumerate(base)
        ]
        somme = sum(base)
        base = [valeur / somme for valeur in base]

    return base


def tirer_horodatage(jour: date, flux: str, generateur: np.random.Generator) -> datetime:
    profil = profil_horaire_applicable(jour, flux)
    heure = int(generateur.choice(24, p=profil))
    minute = int(generateur.integers(0, 60))
    seconde = int(generateur.integers(0, 60))
    return datetime(jour.year, jour.month, jour.day, heure, minute, seconde)
