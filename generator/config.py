"""Charge la configuration du générateur depuis generator/config/*.yml.

Chaque fichier porte une clé racine `parametres`, une liste d'entrées portant
chacune six clés : nom, valeur, unite, provenance, preuve, note. La
complétude d'une entrée se contrôle par la présence de ces clés, jamais par
la véracité de leur valeur : une entrée dont `valeur` vaut 0, "" ou [] est
complète et légitime.

Le résultat de l'analyse YAML est mémorisé par répertoire : un répertoire
donné n'est analysé qu'une fois par processus, et chaque appel rend une copie
indépendante pour qu'aucun appelant ne puisse corrompre la mémorisation en
modifiant la structure rendue. `vider_cache()` efface cette mémorisation ;
elle ne sert à rien en production, seulement aux tests qui écrivent un
fichier de configuration en cours de processus et doivent en relire le
contenu à jour.
"""

import copy
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent
DOSSIER_CONFIG = RACINE / "config"

CLES_OBLIGATOIRES = ["nom", "valeur", "unite", "provenance", "preuve", "note"]

_CACHE_ENTREES: dict[Path, list[dict]] = {}


def fichiers_configuration(dossier: Path = DOSSIER_CONFIG) -> list[Path]:
    return sorted(dossier.glob("*.yml"))


def vider_cache() -> None:
    _CACHE_ENTREES.clear()


def charger_entrees(dossier: Path = DOSSIER_CONFIG) -> list[dict]:
    dossier = Path(dossier)
    if dossier not in _CACHE_ENTREES:
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
        _CACHE_ENTREES[dossier] = entrees
    return copy.deepcopy(_CACHE_ENTREES[dossier])


def valeur(nom: str, dossier: Path = DOSSIER_CONFIG):
    for entree in charger_entrees(dossier):
        if entree["nom"] == nom:
            return entree["valeur"]
    raise KeyError(f"paramètre inconnu : {nom}")
