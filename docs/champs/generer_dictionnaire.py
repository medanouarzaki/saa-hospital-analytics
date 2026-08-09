"""Rend docs/champs/registre_champs.yml en dictionnaire des données, Markdown et LaTeX."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"
CIBLE_MD = RACINE / "docs" / "champs" / "dictionnaire_donnees.md"
CIBLE_TEX = RACINE / "report" / "dictionnaire_donnees.tex"

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


def main() -> None:
    with REGISTRE.open(encoding="utf-8") as f:
        entrees = yaml.safe_load(f)

    tables = grouper_par_table(entrees)

    CIBLE_MD.parent.mkdir(parents=True, exist_ok=True)
    CIBLE_MD.write_text(rendre_markdown(tables), encoding="utf-8")

    CIBLE_TEX.parent.mkdir(parents=True, exist_ok=True)
    CIBLE_TEX.write_text(rendre_tex(tables), encoding="utf-8")


if __name__ == "__main__":
    main()
