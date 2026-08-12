"""Fabrique de générateur aléatoire, lue depuis generator/config/execution.yml.

Toute fonction stochastique du générateur reçoit son propre générateur en
argument ; aucune ne s'appuie sur un état global implicite, ce qui est ce qui
rend la reproductibilité vérifiable.
"""

import numpy as np

from generator import config

ALGORITHMES = {
    "PCG64": np.random.PCG64,
}


def construire_generateur(graine: int | None = None) -> np.random.Generator:
    entrees = {e["nom"]: e for e in config.charger_entrees()}
    if graine is None:
        graine = entrees["graine_aleatoire"]["valeur"]
    nom_algorithme = entrees["algorithme_generateur"]["valeur"]
    bit_generator = ALGORITHMES[nom_algorithme](graine)
    return np.random.Generator(bit_generator)
