"""Lit le registre des champs (docs/champs/registre_champs.yml).

Mémorisé selon le même principe que generator/config.py : une lecture par
chemin et par processus, une copie indépendante à chaque appel, et un
vidage explicite réservé aux tests qui doivent relire un registre modifié.
"""

import copy
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"

_CACHE_REGISTRE: dict[Path, list[dict]] = {}


def vider_cache() -> None:
    _CACHE_REGISTRE.clear()


def _entrees(chemin: Path = CHEMIN_REGISTRE) -> list[dict]:
    chemin = Path(chemin)
    if chemin not in _CACHE_REGISTRE:
        with chemin.open(encoding="utf-8") as f:
            _CACHE_REGISTRE[chemin] = yaml.safe_load(f)
    return copy.deepcopy(_CACHE_REGISTRE[chemin])


def noms_tables(chemin: Path = CHEMIN_REGISTRE) -> list[str]:
    noms = []
    for entree in _entrees(chemin):
        if entree["table"] not in noms:
            noms.append(entree["table"])
    return noms


def colonnes_table(table: str, chemin: Path = CHEMIN_REGISTRE) -> list[str]:
    return [e["colonne"] for e in _entrees(chemin) if e["table"] == table]


def type_metier(table: str, colonne: str, chemin: Path = CHEMIN_REGISTRE) -> str:
    for entree in _entrees(chemin):
        if entree["table"] == table and entree["colonne"] == colonne:
            return entree["type_metier"]
    raise KeyError(f"colonne inconnue : {table}.{colonne}")
