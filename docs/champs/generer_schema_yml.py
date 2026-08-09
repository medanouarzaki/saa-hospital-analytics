"""Rend docs/champs/registre_champs.yml en fichier de sources dbt."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"


def grouper_par_table(entrees: list[dict]) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for entree in entrees:
        tables.setdefault(entree["table"], []).append(entree)
    return tables


def rendre_colonne(colonne: dict) -> dict:
    return {
        "name": colonne["colonne"],
        "description": colonne["note"],
        "meta": {
            "provenance": colonne["provenance"],
            "preuve": colonne["preuve"],
            "type_metier": colonne["type_metier"],
        },
    }


def generer(racine: Path = RACINE) -> None:
    with REGISTRE.open(encoding="utf-8") as f:
        entrees = yaml.safe_load(f)

    tables = grouper_par_table(entrees)

    schema = {
        "version": 2,
        "sources": [
            {
                "name": "source",
                "tables": [
                    {
                        "name": table.removeprefix("source."),
                        "columns": [rendre_colonne(c) for c in colonnes],
                    }
                    for table, colonnes in tables.items()
                ],
            }
        ],
    }

    cible = racine / "dbt" / "models" / "sources" / "source.yml"
    cible.parent.mkdir(parents=True, exist_ok=True)
    with cible.open("w", encoding="utf-8") as f:
        f.write("# Fichier produit mécaniquement depuis le registre des champs : ne pas\n")
        f.write("# modifier à la main.\n")
        yaml.safe_dump(schema, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    generer()
