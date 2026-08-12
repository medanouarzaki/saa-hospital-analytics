"""Accède aux nomenclatures (domaines de valeurs des colonnes codées).

Lit generator/config/*.yml par le chargeur existant, dont la mémorisation par
répertoire est déjà en place : ce module n'en ajoute pas une seconde. Chaque
fonction accepte en argument optionnel les entrées déjà chargées, pour que
l'appelant qui interroge la même colonne à chaque ligne écrite ne recopie pas
la configuration à chaque appel.
"""

from generator import config

PREFIXE_NOMENCLATURE = "nomenclature_"


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def noms_nomenclatures(entrees: dict[str, dict] | None = None) -> list[str]:
    entrees = _entrees(entrees)
    return sorted(nom for nom in entrees if nom.startswith(PREFIXE_NOMENCLATURE))


def codes_nomenclature(nom: str, entrees: dict[str, dict] | None = None) -> list[str]:
    entrees = _entrees(entrees)
    if nom not in entrees:
        raise KeyError(f"nomenclature inconnue : {nom}")
    return [couple["code"] for couple in entrees[nom]["valeur"]]


def libelle(nom: str, code: str, entrees: dict[str, dict] | None = None) -> str:
    entrees = _entrees(entrees)
    if nom not in entrees:
        raise KeyError(f"nomenclature inconnue : {nom}")
    for couple in entrees[nom]["valeur"]:
        if couple["code"] == code:
            return couple["libelle"]
    raise KeyError(f"code absent de {nom} : {code!r}")


def nomenclature_colonne(table: str, colonne: str, entrees: dict[str, dict] | None = None) -> str:
    entrees = _entrees(entrees)

    differees = entrees["colonnes_differees"]["valeur"]
    if any(c["table"] == table and c["colonne"] == colonne for c in differees):
        raise KeyError(f"colonne différée, sans nomenclature encore établie : {table}.{colonne}")

    correspondance = entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    for c in correspondance:
        if c["table"] == table and c["colonne"] == colonne:
            return c["nomenclature"]

    raise KeyError(f"colonne sans nomenclature (identifiant ou inconnue) : {table}.{colonne}")
