"""Rend le registre des chiffres en commandes LaTeX, une par entrée.

Le rapport n'écrit jamais une valeur : il écrit `\\chiffre{identifiant}`, et la valeur vient d'ici.
Un identifiant inconnu produit une erreur de compilation nommant l'identifiant, plutôt qu'un blanc
silencieux dans le texte.

Le formatage est fait ici, une fois : les entiers reçoivent une espace fine insécable tous les trois
chiffres, comme l'usage typographique français le demande, et les décimaux une virgule.
"""

from __future__ import annotations

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent
SOURCE = RACINE / "registre_chiffres.yml"
CIBLE = RACINE.parent.parent / "report" / "chiffres.tex"

ENTETE = r"""% Fichier produit mécaniquement à partir de docs/chiffres/registre_chiffres.yml.
% Ne pas modifier à la main : docs/chiffres/generer_chiffres_tex.py le réécrit.
%
% Le rapport n'écrit aucune valeur en clair. Il écrit \chiffre{identifiant}, et la valeur vient
% d'ici, mesurée par la commande que le registre porte en regard de cet identifiant.
%
% Un identifiant inconnu déclenche une erreur de compilation qui le nomme : un chiffre absent doit
% arrêter la composition, jamais laisser un blanc dans une phrase.

\newcommand{\chiffre}[1]{%
  \ifcsname chiffre@#1\endcsname
    \csname chiffre@#1\endcsname
  \else
    \GenericError{}{Chiffre inconnu : #1}{}{Cet identifiant n'existe pas au registre des chiffres.}%
  \fi
}

"""


def formater(valeur, unite: str) -> str:
    """Un entier prend ses séparateurs de milliers ; un décimal prend la virgule."""
    if isinstance(valeur, bool):
        return str(valeur)
    if isinstance(valeur, int):
        chiffres = f"{valeur:,}".replace(",", r"\,")
        return chiffres
    if isinstance(valeur, float):
        texte = repr(valeur).rstrip("0").rstrip(".")
        return texte.replace(".", ",")
    return str(valeur)


def rendre(registre: dict) -> str:
    lignes = [ENTETE]
    for entree in registre["chiffres"]:
        valeur = formater(entree["valeur"], entree["unite"])
        lignes.append(
            r"\expandafter\def\csname chiffre@" + entree["id"] + r"\endcsname{" + valeur + "}"
        )
    return "\n".join(lignes) + "\n"


def main() -> None:
    with SOURCE.open(encoding="utf-8") as fichier:
        registre = yaml.safe_load(fichier)
    CIBLE.write_text(rendre(registre), encoding="utf-8")
    print(f"{len(registre['chiffres'])} chiffre(s) rendus dans {CIBLE.name}")


if __name__ == "__main__":
    main()
