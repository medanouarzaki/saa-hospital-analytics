"""Rend le registre des chiffres en commandes LaTeX, une par entrée — scalaires ET séries.

Le rapport n'écrit jamais une valeur : il écrit `\\chiffre{identifiant}`, et la valeur vient d'ici.
Un identifiant inconnu produit une erreur de compilation nommant l'identifiant, plutôt qu'un blanc
silencieux dans le texte.

Le formatage est fait ici, une fois : les entiers reçoivent une espace fine insécable tous les trois
chiffres, comme l'usage typographique français le demande, et les décimaux une virgule.

UNE SÉRIE S'APPELLE DE LA MÊME FAÇON, ET C'EST TOUT L'INTÉRÊT : `\\serie{identifiant}` s'étend au
chemin du fichier de données, celui que `\\addplot table` et `\\pgfplotstabletypeset` reçoivent. Un
identifiant de série inconnu arrête la composition en le nommant, exactement comme un scalaire
inconnu. Aucune convention de plus n'est créée : un seul registre, un seul fichier produit, deux
commandes qui se lisent pareil.
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

% Le chemin du fichier de données d'une série, relatif au répertoire de composition. Aucune donnée
% n'est tapée dans une source du rapport : un graphique et un tableau lisent ce fichier, que seule
% la commande consignée au registre écrit.
\newcommand{\serie}[1]{%
  \ifcsname serie@#1\endcsname
    \csname serie@#1\endcsname
  \else
    \GenericError{}{Serie inconnue : #1}{}{Cet identifiant n'existe pas au registre des chiffres.}%
  \fi
}

"""


def formater(valeur, unite: str, decimales: int | None = None) -> str:
    """Un nombre prend ses séparateurs de milliers ; un décimal prend en plus la virgule.

    TROIS RÈGLES, ET LES TROIS SONT MESURÉES SUR LE RENDU. La partie entière d'un décimal reçoit le
    même groupement que celle d'un entier — sans quoi une même page écrivait « 21 066 factures » et
    « 6519554,3 dirhams ». Un nombre négatif reçoit le signe MOINS — écrit sans accolade, pour que
    le motif du contrôle qui lit ce fichier reste capable d'y délimiter la valeur — et non le trait
    d'union, qui est un autre caractère et se compose plus court. Un zéro de fin est retiré, mais
    jamais au point de manger un zéro significatif de la partie entière.

    UNE QUATRIÈME RÈGLE, ET ELLE NE TOUCHE QUE L'AFFICHAGE. Une entrée peut porter `decimales` :
    la valeur consignée reste celle que la commande a rendue — c'est elle que la remesure compare,
    à l'égalité stricte —, et seul son RENDU est arrondi. Le motif est mesuré : cinq entrées du
    registre portent de douze à seize décimales, et une marge écrite « 270,868434285775 » sur une
    planche projetée ne se lit pas. Arrondir la valeur consignée aurait été une autre chose, et une
    faute : la remesure aurait rougi sur une valeur juste.
    """
    if isinstance(valeur, bool):
        return str(valeur)
    if not isinstance(valeur, (int, float)):
        return str(valeur)

    signe = "$-$" if valeur < 0 else ""
    absolue = abs(valeur)
    if isinstance(valeur, int):
        return signe + f"{absolue:,}".replace(",", r"\,")

    texte = f"{absolue:.{decimales}f}" if decimales is not None else repr(absolue)
    entiere, _, decimale = texte.partition(".")
    if decimales is None:
        decimale = decimale.rstrip("0")
    entiere = f"{int(entiere):,}".replace(",", r"\,")
    return signe + (entiere + "," + decimale if decimale else entiere)


def rendre(registre: dict) -> str:
    lignes = [ENTETE]
    for entree in registre["chiffres"]:
        valeur = formater(entree["valeur"], entree["unite"], entree.get("decimales"))
        lignes.append(
            r"\expandafter\def\csname chiffre@" + entree["id"] + r"\endcsname{" + valeur + "}"
        )
    lignes.append("")
    for serie in registre.get("series", []):
        lignes.append(
            r"\expandafter\def\csname serie@"
            + serie["id"]
            + r"\endcsname{"
            + serie["fichier"]
            + "}"
        )
    return "\n".join(lignes) + "\n"


def main() -> None:
    with SOURCE.open(encoding="utf-8") as fichier:
        registre = yaml.safe_load(fichier)
    CIBLE.write_text(rendre(registre), encoding="utf-8")
    print(
        f"{len(registre['chiffres'])} chiffre(s) et {len(registre.get('series', []))} série(s) "
        f"rendus dans {CIBLE.name}"
    )


if __name__ == "__main__":
    main()
