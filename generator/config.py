"""Charge la configuration du générateur depuis generator/config/*.yml.

Chaque fichier porte une clé racine `parametres`, une liste d'entrées portant
chacune six clés : nom, valeur, unite, provenance, preuve, note. La
complétude d'une entrée se contrôle par la présence de ces clés, jamais par
la véracité de leur valeur : une entrée dont `valeur` vaut 0, "" ou [] est
complète et légitime.
"""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent
DOSSIER_CONFIG = RACINE / "config"

CLES_OBLIGATOIRES = ["nom", "valeur", "unite", "provenance", "preuve", "note"]


def fichiers_configuration(dossier: Path = DOSSIER_CONFIG) -> list[Path]:
    return sorted(dossier.glob("*.yml"))


def charger_entrees(dossier: Path = DOSSIER_CONFIG) -> list[dict]:
    entrees = []
    for fichier in fichiers_configuration(dossier):
        with fichier.open(encoding="utf-8") as f:
            contenu = yaml.safe_load(f)
        for entree in contenu["parametres"]:
            manquantes = [cle for cle in CLES_OBLIGATOIRES if cle not in entree]
            if manquantes:
                raise ValueError(
                    f"{fichier.name} : entrée '{entree.get('nom', '?')}' incomplète, "
                    f"clés manquantes {manquantes}"
                )
            entrees.append(entree)
    return entrees


def valeur(nom: str, dossier: Path = DOSSIER_CONFIG):
    for entree in charger_entrees(dossier):
        if entree["nom"] == nom:
            return entree["valeur"]
    raise KeyError(f"paramètre inconnu : {nom}")
