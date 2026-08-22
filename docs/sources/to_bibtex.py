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


# Une empreinte cryptographique est un mot d'une longueur qu'aucune colonne ne peut porter, et
# qu'aucun mécanisme de coupure ne sait rompre : elle n'offre ni tiret, ni point, ni changement de
# classe de caractères où couper. Mesuré au rendu : l'empreinte SHA-256 d'une source SORTAIT DE LA
# FEUILLE, une trentaine de caractères perdus au-delà du bord de la page.
#
# `\nolinkurl` la compose en chasse fixe et autorise la coupure n'importe où, `xurl` étant chargé
# par le document. Le seuil de trente-deux caractères hexadécimaux ne touche aucun mot du français
# ni aucun identifiant du projet.
EMPREINTE = re.compile(r"\b[0-9a-f]{32,}\b")


def envelopper_empreintes(texte: str) -> str:
    return EMPREINTE.sub(lambda m: r"\nolinkurl{" + m.group(0) + "}", texte)


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
        # L'ADRESSE VA AU CHAMP `url`, ET NON À `howpublished`, ET LA RELECTURE DU DOCUMENT
        # COMPOSÉ L'A IMPOSÉ. `howpublished` est un champ de texte ordinaire : biblatex l'imprime
        # tel quel, sans passer par `\url`. Six adresses SORTAIENT DE LA FEUILLE, leur texte perdu
        # au-delà du bord de la page — ni `xurl` ni la marge d'élasticité ne peuvent couper ce que
        # `\url` n'enveloppe pas. Au champ `url`, biblatex les compose en chasse fixe et les coupe.
        #
        # L'adresse n'y est PAS échappée, et c'est la contrepartie exacte : dans `howpublished`,
        # `%` et `_` devaient l'être pour ne pas casser la composition ; sous `\url`, ils doivent
        # rester bruts, faute de quoi `\%20` se compose en `%5C%20` et l'adresse cesse d'être
        # celle qui a été consultée. Mesuré au rendu, puis les vingt-huit adresses confrontées
        # caractère par caractère au registre des sources.
        "url": source["url"],
        "note": envelopper_empreintes(
            echapper_latex(
                f"Consulté le {source['date_consultation']}. {source.get('note', '')}".strip()
            )
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
    # moins inexact.
    #
    # Ce résidu (avertissement sur les entrées non_datee) n'apparaît qu'avec
    # l'option --validate-datamodel de biber, optionnelle. `biber --tool` en
    # usage normal, sans cette stricture, ne signale ni avertissement ni
    # erreur sur le fichier produit.

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
