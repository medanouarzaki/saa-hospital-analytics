"""Rend docs/champs/registre_champs.yml en dictionnaire des données, et en synthèse.

TROIS SORTIES, UNE SEULE SOURCE. Le dictionnaire complet en Markdown pour le dépôt, le même en
LaTeX, et une SYNTHÈSE en LaTeX que le rapport compose à la place du dictionnaire complet.

Le motif de la synthèse est une mesure : le dictionnaire complet occupait vingt-trois folios sur
cent deux, soit près d'un quart du document, pour un tableau que personne ne lit en entier. Le
rapport porte désormais la synthèse et renvoie au dictionnaire complet, qui reste un artefact du
dépôt et continue d'être produit à l'identique.

LES TROIS SORTIES VIENNENT DU MÊME MODULE, ET C'EST LA PROPRIÉTÉ QUI COMPTE. Deux fichiers écrits
séparément peuvent diverger ; deux sorties d'une même lecture du registre ne le peuvent pas. Une
table retirée du registre disparaît des trois du même geste.

PAR QUELLE VOIE LA SYNTHÈSE SERAIT-ELLE VERTE ALORS QUE LE REGISTRE AURAIT CHANGÉ ? Une seule, et
elle est fermée : le fichier produit est commis, et rien n'obligeait à le régénérer après une
modification du registre. `tests/test_provenance.py::test_artefacts_synchrones` régénère les
artefacts dans un répertoire temporaire et compare octet pour octet ; la synthèse y a été ajoutée
à la liste des fichiers comparés, au même titre que le dictionnaire dont elle dérive.

CE QUE LA SYNTHÈSE NE PORTE PAS. Le grain de chaque table n'y figure pas : aucune source lisible
par un programme ne le porte. L'écrire à la main dans un fichier produit mécaniquement ferait de
ce fichier un objet à moitié écrit, et c'est exactement ce que la production mécanique évite.
"""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"

ENTETES = ["colonne", "type_metier", "libelle_hosix", "provenance", "preuve", "note"]


def grouper_par_table(entrees: list[dict]) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for entree in entrees:
        tables.setdefault(entree["table"], []).append(entree)
    return tables


def echapper_latex(valeur: str) -> str:
    return (
        valeur.replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def rendre_markdown(tables: dict[str, list[dict]]) -> str:
    lignes = ["# Dictionnaire des données", ""]
    for table, colonnes in tables.items():
        lignes.append(f"## {table}")
        lignes.append("")
        lignes.append("| colonne | type_metier | libelle_hosix | provenance | preuve | note |")
        lignes.append("|---|---|---|---|---|---|")
        for c in colonnes:
            lignes.append(
                f"| {c['colonne']} | {c['type_metier']} | {c['libelle_hosix']} | "
                f"{c['provenance']} | {c['preuve']} | {c['note']} |"
            )
        lignes.append("")
    return "\n".join(lignes).rstrip("\n") + "\n"


ETIQUETTES = ("OBS", "DOC", "HYP")


def compter_par_provenance(colonnes: list[dict]) -> dict[str, int]:
    comptes = dict.fromkeys(ETIQUETTES, 0)
    for c in colonnes:
        comptes[c["provenance"]] += 1
    return comptes


def rendre_synthese_tex(tables: dict[str, list[dict]]) -> str:
    """Une ligne par table : son nom, son nombre de colonnes, et sa répartition de provenance.

    C'est la répartition PAR TABLE qui apprend quelque chose. Savoir qu'une table est entièrement
    observée et qu'une autre repose sur des hypothèses est une information ; la proportion
    d'ensemble en est une autre, et le rapport la donne ailleurs.
    """
    lignes = [
        "% Fichier produit mécaniquement depuis le registre des champs : ne pas",
        "% modifier à la main. Voir docs/champs/generer_dictionnaire.py.",
        "",
        r"\begin{center}",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Table & Colonnes & \texttt{OBS} & \texttt{DOC} & \texttt{HYP} \\",
        r"\midrule",
    ]
    totaux = dict.fromkeys(ETIQUETTES, 0)
    total_colonnes = 0
    for table, colonnes in tables.items():
        comptes = compter_par_provenance(colonnes)
        total_colonnes += len(colonnes)
        for etiquette in ETIQUETTES:
            totaux[etiquette] += comptes[etiquette]
        lignes.append(
            f"{echapper_latex(table)} & {len(colonnes)} & "
            + " & ".join(str(comptes[e]) for e in ETIQUETTES)
            + r" \\"
        )
    lignes.append(r"\midrule")
    lignes.append(
        r"\textbf{Total} & \textbf{"
        + str(total_colonnes)
        + "} & "
        + " & ".join(r"\textbf{" + str(totaux[e]) + "}" for e in ETIQUETTES)
        + r" \\"
    )
    lignes.append(r"\bottomrule")
    lignes.append(r"\end{tabular}")
    lignes.append(r"\end{center}")
    lignes.append("")
    return "\n".join(lignes).rstrip("\n") + "\n"


def rendre_tex(tables: dict[str, list[dict]]) -> str:
    lignes = [
        "% Fichier produit mécaniquement depuis le registre des champs : ne pas",
        "% modifier à la main.",
        "",
    ]
    for table, colonnes in tables.items():
        lignes.append(rf"\subsection*{{{echapper_latex(table)}}}")
        lignes.append(r"\begin{longtable}{p{2.5cm}p{1.8cm}p{2.8cm}p{1.3cm}p{2.2cm}p{5cm}}")
        lignes.append(r"\hline")
        lignes.append(r"Colonne & Type métier & Libellé Hosix & Provenance & Preuve & Note \\")
        lignes.append(r"\hline")
        lignes.append(r"\endhead")
        for c in colonnes:
            lignes.append(
                f"{echapper_latex(c['colonne'])} & "
                f"{echapper_latex(c['type_metier'])} & "
                f"{echapper_latex(c['libelle_hosix'])} & "
                f"{echapper_latex(c['provenance'])} & "
                f"{echapper_latex(c['preuve'])} & "
                f"{echapper_latex(c['note'])} \\\\"
            )
        lignes.append(r"\hline")
        lignes.append(r"\end{longtable}")
        lignes.append("")
    return "\n".join(lignes).rstrip("\n") + "\n"


def generer(racine: Path = RACINE) -> None:
    with REGISTRE.open(encoding="utf-8") as f:
        entrees = yaml.safe_load(f)

    tables = grouper_par_table(entrees)

    cible_md = racine / "docs" / "champs" / "dictionnaire_donnees.md"
    cible_md.parent.mkdir(parents=True, exist_ok=True)
    cible_md.write_text(rendre_markdown(tables), encoding="utf-8")

    cible_tex = racine / "report" / "dictionnaire_donnees.tex"
    cible_tex.parent.mkdir(parents=True, exist_ok=True)
    cible_tex.write_text(rendre_tex(tables), encoding="utf-8")

    cible_synthese = racine / "report" / "dictionnaire_synthese.tex"
    cible_synthese.write_text(rendre_synthese_tex(tables), encoding="utf-8")


if __name__ == "__main__":
    generer()
