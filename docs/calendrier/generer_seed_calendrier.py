"""Rend generator/config/calendrier.yml en seed dbt du calendrier marocain.

Reproduit exactement la logique de generator/calendrier.py (jours_feries,
est_ramadan) : ce module ne réimplémente aucune règle, il relit la même
source de vérité et le même calcul.
"""

import re
from datetime import date, timedelta
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
CALENDRIER = RACINE / "generator" / "config" / "calendrier.yml"
PROJET_DBT = RACINE / "dbt" / "dbt_project.yml"

MOTIF_DATE_MOBILE = re.compile(r"^(ramadan_debut|ramadan_fin|aid_al_fitr|aid_al_adha)_(\d{4})$")


def _entrees() -> dict[str, dict]:
    with CALENDRIER.open(encoding="utf-8") as f:
        parametres = yaml.safe_load(f)["parametres"]
    return {e["nom"]: e for e in parametres}


def _etendue_annees() -> range:
    with PROJET_DBT.open(encoding="utf-8") as f:
        projet = yaml.safe_load(f)
    debut = date.fromisoformat(projet["vars"]["dim_date_debut"])
    fin = date.fromisoformat(projet["vars"]["dim_date_fin"])
    return range(debut.year, fin.year + 1)


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


def lignes(annees: range, entrees: dict[str, dict]) -> list[tuple[date, str, str]]:
    resultat: list[tuple[date, str, str]] = []

    premiere_annee_wahda = entrees["aid_al_wahda_premiere_annee"]["valeur"]
    feries_fixes = _feries_fixes(entrees)
    for annee in annees:
        for nom, (mois, jour) in feries_fixes.items():
            if nom == "ferie_fixe_aid_al_wahda" and annee < premiere_annee_wahda:
                continue
            resultat.append((date(annee, mois, jour), "ferie_fixe", nom))

    duree_aid = entrees["duree_aid_jours"]["valeur"]
    dates_mobiles = _dates_mobiles(entrees)
    for annee in annees:
        mobiles = dates_mobiles.get(annee)
        if not mobiles:
            continue
        for grandeur_debut in ("aid_al_fitr", "aid_al_adha"):
            debut = mobiles[grandeur_debut]
            for decalage in range(duree_aid):
                resultat.append((debut + timedelta(days=decalage), "ferie_mobile", grandeur_debut))
        debut_ramadan, fin_ramadan = mobiles["ramadan_debut"], mobiles["ramadan_fin"]
        jour_courant = debut_ramadan
        while jour_courant <= fin_ramadan:
            resultat.append((jour_courant, "ramadan", "ramadan"))
            jour_courant += timedelta(days=1)

    resultat.sort(key=lambda ligne: (ligne[0].isoformat(), ligne[1], ligne[2]))
    return resultat


def generer(racine: Path = RACINE) -> None:
    entrees = _entrees()
    annees = _etendue_annees()

    cible = racine / "dbt" / "seeds" / "calendrier_marocain.csv"
    cible.parent.mkdir(parents=True, exist_ok=True)
    with cible.open("w", encoding="utf-8", newline="\n") as f:
        f.write("jour,categorie,libelle\n")
        for jour, categorie, libelle in lignes(annees, entrees):
            f.write(f"{jour.isoformat()},{categorie},{libelle}\n")


if __name__ == "__main__":
    generer()
