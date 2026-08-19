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

`fiches_modifiees` fait exception au circuit ci-dessus : ce module ne reçoit ni les lignes de
`source.patients` ni le type de changement métier tiré par `generator/patients.py` (l'appel
d'orchestration, dans `generator/execution.py`, hors du périmètre modifiable ici, ne les
transmet pas). Cette catégorie est donc recalculée ici en relisant les fichiers CSV déjà écrits
par `execution` (`execution.partitions`), après que `generator/defauts.py` a pu altérer ces
mêmes lignes en place : la vérité rapportée est donc toujours celle qui a réellement atteint le
disque, y compris dans le cas rare où un défaut de surface porte sur la même colonne qu'un
changement métier et l'efface — mesuré et documenté à l'introduction de cette
catégorie, pas devinable depuis ce seul fichier.
"""

import csv
from collections import Counter
from pathlib import Path

import yaml

from generator import config, ecriture, patients, registre

NOM_FICHIER = "verite_terrain.yml"

_COLONNES_TECHNIQUES = {"date_extraction", "date_modification", "modifie_par", "n_ipp"}


def _lire_lignes_patients(execution: ecriture.Execution) -> list[dict]:
    chemins_csv = [
        execution.racine / relatif
        for relatif in execution.partitions.get(patients.TABLE, [])
        if relatif.endswith(".csv")
    ]
    lignes: list[dict] = []
    for chemin in chemins_csv:
        with chemin.open(encoding="utf-8", newline="") as f:
            lignes.extend(csv.DictReader(f))
    return lignes


def _type_modification(colonnes_changees: set[str]) -> str | None:
    for type_modification, colonnes_autorisees in patients.COLONNES_PAR_TYPE_MODIFICATION.items():
        if colonnes_changees <= set(colonnes_autorisees):
            return type_modification
    raise ValueError(
        f"colonnes changées {sorted(colonnes_changees)} ne correspondent à aucun type de "
        "changement métier déclaré dans generator/patients.py::COLONNES_PAR_TYPE_MODIFICATION"
    )


def _calculer_fiches_modifiees(execution: ecriture.Execution) -> list[dict]:
    valeur_manquante = config.valeur("valeur_manquante")
    colonnes = [
        colonne
        for colonne in registre.colonnes_table(patients.TABLE)
        if colonne not in _COLONNES_TECHNIQUES
    ]

    par_ipp: dict[str, list[dict]] = {}
    for ligne in _lire_lignes_patients(execution):
        par_ipp.setdefault(ligne["n_ipp"], []).append(ligne)

    entrees: list[dict] = []
    for n_ipp, versions in par_ipp.items():
        if len(versions) != 2:
            continue
        creation, modification = sorted(
            versions, key=lambda v: v["date_modification"] == valeur_manquante, reverse=True
        )

        colonnes_changees = {
            colonne for colonne in colonnes if creation[colonne] != modification[colonne]
        }
        if not colonnes_changees:
            continue

        entrees.append(
            {
                "n_ipp": n_ipp,
                "date_extraction": modification["date_extraction"],
                "type_modification": _type_modification(colonnes_changees),
                "colonnes": {
                    colonne: {"avant": creation[colonne], "apres": modification[colonne]}
                    for colonne in sorted(colonnes_changees)
                },
            }
        )

    return sorted(entrees, key=lambda e: e["n_ipp"])


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

    fiches_modifiees = _calculer_fiches_modifiees(execution)
    contenu["fiches_modifiees"] = {"entrees": fiches_modifiees, "decompte": len(fiches_modifiees)}

    chemin = execution.racine / execution.scenario / NOM_FICHIER
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8") as f:
        yaml.safe_dump(contenu, f, allow_unicode=True, sort_keys=True)
    return chemin
