"""Convertit un volume annuel mesuré en comptes journaliers sur la période de génération.

Ne tire aucun nombre aléatoire : deux appels avec les mêmes arguments rendent le même
résultat. Ne recalcule aucun coefficient de modulation : il appelle le moteur temporel,
qui en reste l'unique source.
"""

from datetime import date, timedelta

from generator import config, temporel

ANNEES = (2024, 2025, 2026)


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _jours_annee(annee: int) -> list[date]:
    debut = date(annee, 1, 1)
    fin = date(annee, 12, 31)
    jours = []
    jour = debut
    while jour <= fin:
        jours.append(jour)
        jour += timedelta(days=1)
    return jours


def _jours_periode(entrees: dict[str, dict]) -> list[date]:
    debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    jours = []
    jour = debut
    while jour <= fin:
        jours.append(jour)
        jour += timedelta(days=1)
    return jours


def rapport_annee_partielle(annee: int, flux: str, entrees: dict[str, dict] | None = None) -> float:
    entrees = _entrees(entrees)
    jours_annee = _jours_annee(annee)
    jours_periode = set(_jours_periode(entrees))

    somme_annee = sum(temporel.poids_jour(jour, flux, entrees) for jour in jours_annee)
    somme_periode = sum(
        temporel.poids_jour(jour, flux, entrees) for jour in jours_annee if jour in jours_periode
    )
    return somme_periode / somme_annee


def comptes_journaliers(
    nom_volume: str,
    taux_urgences_par_jour: float | None = None,
    entrees: dict[str, dict] | None = None,
) -> dict[date, int]:
    entrees = _entrees(entrees)

    correspondance = entrees["correspondance_volume_flux"]["valeur"]
    if nom_volume not in correspondance:
        raise KeyError(f"volume sans correspondance de flux : {nom_volume}")
    flux = correspondance[nom_volume]

    natures = entrees["nature_conversion_volume"]["valeur"]
    if nom_volume not in natures:
        raise KeyError(f"volume sans nature de conversion : {nom_volume}")
    nature = natures[nom_volume]

    if nom_volume == "passages_urgences_par_jour" and taux_urgences_par_jour is not None:
        valeur = taux_urgences_par_jour
    else:
        valeur = entrees[nom_volume]["valeur"]

    jours_periode = _jours_periode(entrees)
    resultat: dict[date, int] = {}

    for annee in ANNEES:
        jours_annee_dans_periode = [jour for jour in jours_periode if jour.year == annee]
        if not jours_annee_dans_periode:
            continue

        if nature == "volume_annuel":
            annee_complete = len(jours_annee_dans_periode) == len(_jours_annee(annee))
            if annee_complete:
                cible = round(valeur)
            else:
                rapport = rapport_annee_partielle(annee, flux, entrees)
                cible = round(valeur * rapport)
        elif nature == "taux_journalier":
            cible = round(valeur * len(jours_annee_dans_periode))
        else:
            raise ValueError(f"nature de conversion inconnue : {nature!r}")

        resultat.update(temporel.repartir_total(cible, jours_annee_dans_periode, flux))

    return resultat
