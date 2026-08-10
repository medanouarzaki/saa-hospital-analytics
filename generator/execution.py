"""Orchestre une exécution complète du générateur, table par table.

Construit le fil des épisodes une seule fois, puis appelle chaque générateur du registre
dans l'ordre de ses dépendances, chacun avec son propre générateur aléatoire, indépendant
des autres et dérivé de la même graine (voir `_generateur_pour`). Le registre est ce qui
rend possible un contrôle générique sur « toute table produite » : une table qui l'ignore
n'est pas testée par ce contrôle, faute d'y figurer. Aucune table n'écrit ses fichiers
elle-même ; ce module est le seul point de passage vers le module d'écriture, de sorte que
ce que les tests génèrent par lui est ce qui sera effectivement produit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from generator import (
    alea,
    config,
    ecriture,
    facturation,
    mouvements,
    parcours,
    passages,
    patients,
    prises_en_charge,
    recouvrement,
    registre,
    urgences,
    volumes,
)
from generator import rendez_vous as rdv

PILOTES = {
    "H": "admissions_annuelles",
    "C": "consultations_specialisees_externes",
    "U": "passages_urgences_par_jour",
}


@dataclass
class Contexte:
    entrees: dict[str, dict]
    episodes: list[dict]
    population: list[dict]
    lignes: dict[str, list[dict]] = field(default_factory=dict)
    meta: dict[str, object] = field(default_factory=dict)


GenerateurTable = Callable[["Contexte", np.random.Generator], list[dict]]


def _generer_patients(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    return patients.generer_lignes(
        contexte.episodes, contexte.population, generateur, entrees=contexte.entrees
    )


def _generer_rendez_vous(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    return rdv.generer_lignes(
        contexte.episodes, contexte.population, generateur, entrees=contexte.entrees
    )


def _generer_passages(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    lignes_rendez_vous = contexte.lignes["source.rendez_vous"]
    return passages.generer_lignes(
        contexte.episodes,
        contexte.population,
        lignes_rendez_vous,
        generateur,
        entrees=contexte.entrees,
    )


def _generer_mouvements(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    lignes_passages = contexte.lignes["source.passages"]
    lignes_patients = contexte.lignes["source.patients"]
    lignes, n_depassements = mouvements.generer_lignes(
        lignes_passages, lignes_patients, generateur, entrees=contexte.entrees
    )
    contexte.meta["mouvements_n_depassements_capacite"] = n_depassements
    return lignes


def _generer_urgences(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    lignes_passages = contexte.lignes["source.passages"]
    return urgences.generer_lignes(lignes_passages, generateur, entrees=contexte.entrees)


def _generer_factures(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    # les trois tables issues de la facturation partagent un seul tirage aleatoire : ce
    # generateur calcule les lignes de facture et les prises en charge, met les deux de
    # cote dans le contexte pour que les generateurs suivants les consomment sans retirer
    # de nombres, et rend les factures apres que la prise en charge en a corrige en place
    # part_organisme et part_patient -- avant l'ecriture du fichier, jamais apres.
    lignes_passages = contexte.lignes["source.passages"]
    lignes_mouvements = contexte.lignes["source.mouvements"]
    lignes_urgences = contexte.lignes["source.passages_urgences"]
    lignes_patients = contexte.lignes["source.patients"]
    lignes_factures, lignes_lignes = facturation.generer_lignes(
        lignes_passages, lignes_mouvements, lignes_urgences, generateur, entrees=contexte.entrees
    )
    lignes_prises_en_charge = prises_en_charge.generer_lignes(
        lignes_factures, lignes_patients, generateur, entrees=contexte.entrees
    )
    lignes_encaissements, lignes_creances, lignes_relances = recouvrement.generer_lignes(
        lignes_factures, generateur, entrees=contexte.entrees
    )
    contexte.meta["lignes_facture_en_attente"] = lignes_lignes
    contexte.meta["prises_en_charge_en_attente"] = lignes_prises_en_charge
    contexte.meta["encaissements_en_attente"] = lignes_encaissements
    contexte.meta["creances_en_attente"] = lignes_creances
    contexte.meta["relances_en_attente"] = lignes_relances
    return lignes_factures


def _generer_lignes_facture(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    del generateur
    return contexte.meta.pop("lignes_facture_en_attente")


def _generer_prises_en_charge(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    del generateur
    return contexte.meta.pop("prises_en_charge_en_attente")


def _generer_encaissements(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    del generateur
    return contexte.meta.pop("encaissements_en_attente")


def _generer_creances(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    del generateur
    return contexte.meta.pop("creances_en_attente")


def _generer_relances(contexte: Contexte, generateur: np.random.Generator) -> list[dict]:
    del generateur
    return contexte.meta.pop("relances_en_attente")


REGISTRE_GENERATEURS: tuple[tuple[str, GenerateurTable], ...] = (
    ("source.patients", _generer_patients),
    ("source.rendez_vous", _generer_rendez_vous),
    ("source.passages", _generer_passages),
    ("source.mouvements", _generer_mouvements),
    ("source.passages_urgences", _generer_urgences),
    ("source.factures", _generer_factures),
    ("source.lignes_facture", _generer_lignes_facture),
    ("source.prises_en_charge", _generer_prises_en_charge),
    ("source.encaissements", _generer_encaissements),
    ("source.creances", _generer_creances),
    ("source.relances", _generer_relances),
)


def tables_couvertes(
    generateurs: tuple[tuple[str, GenerateurTable], ...] = REGISTRE_GENERATEURS,
) -> list[str]:
    return [table for table, _ in generateurs]


def tables_non_couvertes(
    generateurs: tuple[tuple[str, GenerateurTable], ...] = REGISTRE_GENERATEURS,
) -> list[str]:
    couvertes = set(tables_couvertes(generateurs))
    return [table for table in registre.noms_tables() if table not in couvertes]


def _generateur_pour(graine: int, indice: int) -> np.random.Generator:
    # np.random.Generator.spawn(n) rend n enfants indépendants dérivés de la graine de
    # départ ; les k premiers enfants de spawn(n) sont identiques à ceux de spawn(m) pour
    # tout m >= k (propriété du SeedSequence sous-jacent, éprouvée avant écriture, voir le
    # rapport). Reconstruire ici un générateur maître frais et ne demander que les indice+1
    # premiers enfants garantit qu'ajouter une table à la fin du registre ne change aucun
    # des générateurs déjà distribués aux tables qui la précèdent : seul un index de
    # position, jamais la taille totale du registre au moment de l'appel, détermine le
    # générateur rendu à un indice donné.
    rng = alea.construire_generateur(graine)
    return rng.spawn(indice + 1)[indice]


def executer(
    racine: Path,
    graine: int,
    taux_urgences_par_jour: float | None = None,
    generateurs: tuple[tuple[str, GenerateurTable], ...] = REGISTRE_GENERATEURS,
    entrees: dict[str, dict] | None = None,
) -> tuple[ecriture.Execution, Contexte]:
    if entrees is None:
        entrees = {e["nom"]: e for e in config.charger_entrees()}

    if taux_urgences_par_jour is None:
        taux_urgences_par_jour = entrees["passages_urgences_par_jour"]["valeur"]
    scenario = f"scenario_{round(taux_urgences_par_jour)}"

    rng_episodes = _generateur_pour(graine, 0)
    comptes = {
        cat: volumes.comptes_journaliers(
            nom,
            taux_urgences_par_jour=taux_urgences_par_jour if cat == "U" else None,
            entrees=entrees,
        )
        for cat, nom in PILOTES.items()
    }
    episodes, population = parcours.construire_parcours(comptes, rng_episodes, entrees=entrees)

    contexte = Contexte(entrees=entrees, episodes=episodes, population=population)

    execution = ecriture.Execution(
        racine, scenario, graine, entrees["date_debut"]["valeur"], entrees["date_fin"]["valeur"]
    )

    for indice, (table, generer) in enumerate(generateurs):
        rng_table = _generateur_pour(graine, indice + 1)
        lignes = generer(contexte, rng_table)
        contexte.lignes[table] = lignes
        execution.ecrire_table(table, lignes)

    execution.ecrire_manifeste()
    return execution, contexte
