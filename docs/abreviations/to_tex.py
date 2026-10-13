"""Rend docs/abreviations/abreviations.yml en report/liminaires/abreviations.tex.

La liste des abréviations des pages préliminaires n'est jamais écrite à la main : ce module l'écrit
depuis le registre, et `tests/test_abreviations.py` régénère le rendu pour le comparer, octet à
octet, au fichier suivi.

L'ORDRE EST CELUI DE LA CLÉ `cle_de_tri`, et il est écrit ici plutôt que laissé au hasard d'un tri
par défaut. Un tri sur la chaîne brute range les capitales accentuées après le Z et sépare un sigle
de son homologue en minuscules ; la clé retire les accents (décomposition puis suppression des
diacritiques) et ignore la casse, puis départage, à égalité, sur la chaîne brute pour que l'ordre
soit total.

Usage :
    python docs/abreviations/to_tex.py              # écrit report/liminaires/abreviations.tex
    python docs/abreviations/to_tex.py --sortie -   # écrit le rendu sur la sortie standard
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
SOURCE = RACINE / "docs" / "abreviations" / "abreviations.yml"
DESTINATION = RACINE / "report" / "liminaires" / "abreviations.tex"

TITRE = "Liste des abréviations"

ENTETE = rf"""% Fichier produit mécaniquement depuis docs/abreviations/abreviations.yml.
% Ne pas modifier à la main : docs/abreviations/to_tex.py le réécrit.

\clearpage
\phantomsection
\addcontentsline{{toc}}{{chapter}}{{{TITRE}}}
\chapter*{{{TITRE}}}
\markboth{{\MakeUppercase{{{TITRE}}}}}{{\MakeUppercase{{{TITRE}}}}}

\begin{{description}}
"""

PIED = r"""\end{description}
"""


def cle_de_tri(sigle: str) -> tuple[str, str]:
    """Ordre alphabétique insensible aux accents et à la casse, départagé par la chaîne brute."""
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFKD", sigle) if not unicodedata.combining(c)
    )
    return (sans_accent.casefold(), sigle)


def charger(chemin: Path = SOURCE) -> dict:
    return yaml.safe_load(chemin.read_text(encoding="utf-8"))


def rendre(registre: dict) -> str:
    entrees = sorted(registre["abreviations"], key=lambda e: cle_de_tri(e["sigle"]))
    lignes = [f"  \\item[{e['sigle']}] {e['developpe']}" for e in entrees]
    return ENTETE + "\n".join(lignes) + "\n" + PIED


def main(arguments: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Rend le registre des abréviations en liste LaTeX des pages préliminaires."
    )
    analyseur.add_argument(
        "--sortie",
        default=str(DESTINATION),
        help="fichier à écrire (par défaut report/liminaires/abreviations.tex), ou - pour la "
        "sortie standard",
    )
    options = analyseur.parse_args(arguments)
    rendu = rendre(charger())
    if options.sortie == "-":
        sys.stdout.write(rendu)
    else:
        Path(options.sortie).write_text(rendu, encoding="utf-8")
        print(f"{rendu.count(chr(92) + 'item')} abréviation(s) rendue(s) dans {options.sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
