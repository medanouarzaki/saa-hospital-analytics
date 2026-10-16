"""Rend la série « planification » en diagramme de Gantt : report/figures/planification.tex.

La figure n'est jamais dessinée à la main : ce module la dessine depuis le fichier de données de la
série, que seule la commande du registre des chiffres écrit, et `tests/test_planification.py`
régénère le rendu pour le comparer, octet à octet, au fichier suivi.

LES SEMAINES VIENNENT DE LA SÉRIE, ET D'ELLE SEULE. Les colonnes vont de la plus petite à la plus
grande semaine que la série porte ; chaque libellé de colonne est produit ici depuis ce numéro. Une
ligne d'origine « jalon » est dessinée en losange, sur sa propre ligne, au-dessus des phases ; les
autres lignes sont des barres, dans l'ordre de la série, qui est celui du tableau des phases.

Usage :
    python docs/planification/to_tex.py              # écrit report/figures/planification.tex
    python docs/planification/to_tex.py --sortie -   # écrit le rendu sur la sortie standard
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
SOURCE = RACINE / "report" / "figures" / "planification.csv"
DESTINATION = RACINE / "report" / "figures" / "planification.tex"

JALON = "jalon"

# Largeur d'une semaine et hauteur d'une ligne, en centimètres. Les noms tiennent sur une ligne :
# une colonne de noms à largeur fixe les coupait et faisait chevaucher deux lignes voisines.
SEMAINE = 1.1
LIGNE = 0.5

ENTETE = r"""% Fichier produit mécaniquement depuis la série « planification » du registre.
% Ne pas modifier à la main : docs/planification/to_tex.py le réécrit.
"""


def charger(chemin: Path = SOURCE) -> list[dict]:
    with chemin.open(encoding="utf-8", newline="") as fichier:
        return list(csv.DictReader(fichier))


def rendre(lignes: list[dict]) -> str:
    semaines = [int(v) for ligne in lignes for v in (ligne["debut"], ligne["fin"])]
    premiere, derniere = min(semaines), max(semaines)
    colonnes = range(premiere, derniere + 1)
    jalons = [ligne for ligne in lignes if ligne["origine"] == JALON]
    phases = [ligne for ligne in lignes if ligne["origine"] != JALON]
    rangs = len(jalons) + len(phases)

    sortie = [ENTETE, rf"\begin{{tikzpicture}}[x={SEMAINE}cm, y=-{LIGNE}cm, font=\footnotesize]"]
    for i, semaine in enumerate(colonnes):
        sortie.append(rf"\node[anchor=south, font=\footnotesize] at ({i + 0.5}, 0) {{S{semaine}}};")
        sortie.append(rf"\draw[griscartouche, line width=0.3pt] ({i}, 0) -- ({i}, {rangs});")
    bord = len(colonnes)
    sortie.append(rf"\draw[griscartouche, line width=0.3pt] ({bord}, 0) -- ({bord}, {rangs});")
    rang = 0
    for jalon in jalons:
        x = int(jalon["debut"]) - premiere + 0.5
        sortie.append(
            rf"\node[anchor=east, font=\footnotesize\itshape] "
            rf"at (-0.1, {rang + 0.5}) {{{jalon['phase']}}};"
        )
        sortie.append(
            rf"\node[diamond, fill=accentgarde, inner sep=2.4pt] at ({x}, {rang + 0.5}) {{}};"
        )
        rang += 1
    for phase in phases:
        debut = int(phase["debut"]) - premiere
        fin = int(phase["fin"]) - premiere + 1
        sortie.append(
            rf"\node[anchor=east] "
            rf"at (-0.1, {rang + 0.5}) {{{phase['phase']}}};"
        )
        sortie.append(rf"\fill[accentgarde!75] ({debut}, {rang}.2) rectangle ({fin}, {rang}.8);")
        rang += 1
    sortie.append(r"\end{tikzpicture}")
    return "\n".join(sortie) + "\n"


def main(arguments: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Rend la série de planification en diagramme de Gantt pour le rapport."
    )
    analyseur.add_argument(
        "--sortie",
        default=str(DESTINATION),
        help="fichier à écrire (par défaut report/figures/planification.tex), ou - pour la "
        "sortie standard",
    )
    options = analyseur.parse_args(arguments)
    rendu = rendre(charger())
    if options.sortie == "-":
        sys.stdout.write(rendu)
    else:
        Path(options.sortie).write_text(rendu, encoding="utf-8")
        print(f"{rendu.count(chr(92) + 'fill')} barre(s) rendue(s) dans {options.sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
