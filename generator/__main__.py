"""Point d'entrée en ligne de commande du générateur.

Mince : ne porte aucune logique de génération, seulement l'analyse des arguments et l'appel
à `generator.execution.executer`. La période et la graine par défaut viennent de la
configuration suivie (`generator/config/`), lue par le mécanisme existant
(`generator.config.charger_entrees`) ; `--date-debut`/`--date-fin` ne font que surcharger le
dictionnaire `entrees` en mémoire, jamais un fichier de `generator/config/`.
"""

import argparse
from pathlib import Path

from generator import config, execution


def main(argv: list[str] | None = None) -> None:
    entrees_defaut = {e["nom"]: e for e in config.charger_entrees()}

    analyseur = argparse.ArgumentParser(
        prog="python -m generator",
        description="Génère un scénario complet (ou une période réduite) vers `racine`.",
    )
    analyseur.add_argument("racine", type=Path, help="Répertoire de sortie de la génération")
    analyseur.add_argument(
        "--graine",
        type=int,
        default=entrees_defaut["graine_aleatoire"]["valeur"],
        help="Graine aléatoire (défaut : graine_aleatoire de la configuration)",
    )
    analyseur.add_argument(
        "--date-debut", metavar="AAAA-MM-JJ", help="Surcharge la date de début de période"
    )
    analyseur.add_argument(
        "--date-fin", metavar="AAAA-MM-JJ", help="Surcharge la date de fin de période"
    )
    arguments = analyseur.parse_args(argv)

    entrees = dict(entrees_defaut)
    if arguments.date_debut is not None:
        entrees["date_debut"] = dict(entrees["date_debut"])
        entrees["date_debut"]["valeur"] = arguments.date_debut
    if arguments.date_fin is not None:
        entrees["date_fin"] = dict(entrees["date_fin"])
        entrees["date_fin"]["valeur"] = arguments.date_fin

    execution_obj, contexte = execution.executer(
        arguments.racine, arguments.graine, entrees=entrees
    )

    print(f"scenario: {execution_obj.scenario}")
    for table, lignes in contexte.lignes.items():
        print(f"  {table}: {len(lignes)} lignes")


if __name__ == "__main__":
    main()
