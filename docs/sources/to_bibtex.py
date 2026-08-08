"""Convertit docs/sources/sources.yml en report/biblio.bib."""

import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
SOURCE = RACINE / "docs" / "sources" / "sources.yml"
DESTINATION = RACINE / "report" / "biblio.bib"

LATEX_SPECIAUX = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def echapper_latex(texte: str) -> str:
    motif = re.compile("|".join(re.escape(c) for c in LATEX_SPECIAUX))
    return motif.sub(lambda m: LATEX_SPECIAUX[m.group(0)], texte)


def cle_bibtex(identifiant: str) -> str:
    return identifiant.lower().replace("-", "")


def construire_entree(source: dict) -> str:
    cle = cle_bibtex(source["id"])
    # author est un champ "names" pour biblatex/biber : une valeur libre contenant
    # plusieurs virgules (listes d'auteurs, "et al.") est interprétée comme une
    # liste de noms au format BibTeX "Nom, Prénom" et casse l'analyse si elle ne
    # s'y conforme pas. Le double accolage {{...}} force un champ littéral, non
    # analysé comme liste de noms.
    champs = {
        "title": echapper_latex(source["titre"]),
        "author": "{" + echapper_latex(source["auteur"]) + "}",
        "howpublished": echapper_latex(source["url"]),
        "note": echapper_latex(
            f"Consulté le {source['date_consultation']}. {source.get('note', '')}".strip()
        ),
    }
    if source["date_publication"] != "non_datee":
        annee_match = re.match(r"(\d{4})", source["date_publication"])
        if annee_match:
            champs["year"] = annee_match.group(1)
    # Aucun champ year n'est écrit pour une entrée non_datee : le modèle de
    # données @misc de biblatex exige un champ date/year valide (un entier),
    # et aucune valeur de repli honnête (ni vide, ni "n.d.") ne satisfait
    # cette contrainte sans fabriquer une date. L'omission est le choix le
    # moins inexact ; le résidu d'avertissement biber en est la conséquence
    # mesurée et documentée à l'étape 5 du rapport, pas une négligence.

    lignes = [f"@misc{{{cle},"]
    for nom_champ, valeur in champs.items():
        lignes.append(f"  {nom_champ} = {{{valeur}}},")
    lignes.append("}")
    return "\n".join(lignes)


def main() -> None:
    with open(SOURCE, encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    convertibles = [s for s in sources if s["verification"] != "introuvable"]
    ecartees = len(sources) - len(convertibles)

    entrees = [construire_entree(s) for s in convertibles]

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with open(DESTINATION, "w", encoding="utf-8") as f:
        f.write("\n\n".join(entrees))
        f.write("\n")

    print(f"entrées converties : {len(convertibles)}")
    print(f"entrées écartées (verification=introuvable) : {ecartees}")


if __name__ == "__main__":
    main()
