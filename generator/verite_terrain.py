"""Écrit le fichier de vérité terrain d'une exécution, sous son répertoire de sortie.

N'est lu par aucun module de génération ni de traitement : sert exclusivement à
l'évaluation d'un bloc ultérieur (le rapprochement probabiliste, la quarantaine). Vit sous
le sous-répertoire de scénario de l'exécution, hors de toute table du registre, et n'est
jamais suivi par le gestionnaire de versions (`generator/output/*` est ignoré).

Chaque catégorie de défaut occupe sa propre clé de premier niveau, à côté de `doublons` :
`champs_manquants`, `absence_structurelle`, `defauts_surface`, `dates_aberrantes`,
`ages_incoherents`, `rdv_doublon_creneau`, `factures_sans_pec` (voir
`generator/defauts.py::injecter_defauts`). Une catégorie future occuperait de même sa propre
clé sœur, sans jamais restructurer une clé déjà écrite.
"""

from collections import Counter
from pathlib import Path

import yaml

from generator import ecriture

NOM_FICHIER = "verite_terrain.yml"


def ecrire(
    execution: ecriture.Execution,
    paires_doublons: list[dict],
    alterations: dict[str, list[dict]] | None = None,
) -> Path:
    alterations = alterations or {}

    decompte_par_variation: Counter = Counter()
    for paire in paires_doublons:
        for variation in paire["variations"]:
            decompte_par_variation[variation] += 1

    contenu = {
        "scenario": execution.scenario,
        "graine": execution.graine,
        "periode": {"debut": execution.date_debut, "fin": execution.date_fin},
        "doublons": {
            "paires": [
                {
                    "n_ipp_1": paire["n_ipp_1"],
                    "n_ipp_2": paire["n_ipp_2"],
                    "variations": list(paire["variations"]),
                }
                for paire in paires_doublons
            ],
            "decompte_par_variation": dict(decompte_par_variation),
        },
    }

    for categorie, entrees in alterations.items():
        contenu[categorie] = {"entrees": entrees, "decompte": len(entrees)}

    chemin = execution.racine / execution.scenario / NOM_FICHIER
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8") as f:
        yaml.safe_dump(contenu, f, allow_unicode=True, sort_keys=True)
    return chemin
