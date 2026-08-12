"""Consultation du calendrier marocain, lu depuis generator/config/calendrier.yml.

Aucune date ni aucune règle de calendrier lunaire n'est portée par ce module :
tout vient du fichier de configuration, par le chargeur générique.
"""

import re
from datetime import date, timedelta

from generator import config

MOTIF_DATE_MOBILE = re.compile(r"^(ramadan_debut|ramadan_fin|aid_al_fitr|aid_al_adha)_(\d{4})$")


def _entrees() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def _feries_fixes(entrees: dict[str, dict]) -> dict[str, tuple[int, int]]:
    feries = {}
    for nom, entree in entrees.items():
        if nom.startswith("ferie_fixe_"):
            mois, jour = (int(partie) for partie in entree["valeur"].split("-"))
            feries[nom] = (mois, jour)
    return feries


def _dates_mobiles(entrees: dict[str, dict]) -> dict[int, dict[str, date]]:
    mobiles: dict[int, dict[str, date]] = {}
    for nom, entree in entrees.items():
        correspondance = MOTIF_DATE_MOBILE.match(nom)
        if correspondance:
            grandeur, annee = correspondance.group(1), int(correspondance.group(2))
            mobiles.setdefault(annee, {})[grandeur] = date.fromisoformat(entree["valeur"])
    return mobiles


def jours_feries(annee: int) -> set[date]:
    entrees = _entrees()
    resultat: set[date] = set()

    premiere_annee_wahda = entrees["aid_al_wahda_premiere_annee"]["valeur"]
    for nom, (mois, jour) in _feries_fixes(entrees).items():
        if nom == "ferie_fixe_aid_al_wahda" and annee < premiere_annee_wahda:
            continue
        resultat.add(date(annee, mois, jour))

    duree_aid = entrees["duree_aid_jours"]["valeur"]
    mobiles = _dates_mobiles(entrees).get(annee)
    if mobiles:
        for grandeur_debut in ("aid_al_fitr", "aid_al_adha"):
            debut = mobiles[grandeur_debut]
            for decalage in range(duree_aid):
                resultat.add(debut + timedelta(days=decalage))

    return resultat


def est_ferie(jour: date) -> bool:
    return jour in jours_feries(jour.year)


def _periode_ramadan(annee: int) -> tuple[date, date] | None:
    mobiles = _dates_mobiles(_entrees()).get(annee)
    if mobiles is None:
        return None
    return mobiles["ramadan_debut"], mobiles["ramadan_fin"]


def est_ramadan(jour: date) -> bool:
    periode = _periode_ramadan(jour.year)
    if periode is None:
        return False
    debut, fin = periode
    return debut <= jour <= fin


def rang_ramadan(jour: date) -> int | None:
    periode = _periode_ramadan(jour.year)
    if periode is None:
        return None
    debut, fin = periode
    if not (debut <= jour <= fin):
        return None
    return (jour - debut).days + 1
