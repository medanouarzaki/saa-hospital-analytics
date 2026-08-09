"""Rend docs/champs/registre_champs.yml en DDL du schéma source, un fichier par table."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"

ENTETE_SCHEMA = """\
-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.
--
-- Ce fichier, et les onze fichiers de table qui le suivent, reconstruisent
-- intégralement le schéma source à chaque application, ils ne le font pas
-- évoluer par différences : chaque table est supprimée avant d'être
-- recréée.
--
-- Aucune contrainte n'est posée : ni clé primaire, ni clause d'obligation
-- de valeur, ni clé étrangère, ni index. La couche source reproduit une
-- extraction et doit accepter ce qu'une extraction contient, y compris des
-- doublons et des valeurs mal formées ; l'unicité et le typage se
-- contrôlent à la couche intermédiaire, avec mise en quarantaine. Une
-- contrainte ici rejetterait précisément les défauts que la chaîne existe
-- pour traiter.
"""

ENTETE_TABLE = """\
-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.
"""


def echapper_sql(valeur: str) -> str:
    return valeur.replace("'", "''")


def grouper_par_table(entrees: list[dict]) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for entree in entrees:
        tables.setdefault(entree["table"], []).append(entree)
    return tables


def rendre_creation(table: str, colonnes: list[dict]) -> list[str]:
    lignes = [f"drop table if exists {table} cascade;", f"create table {table} ("]
    for i, colonne in enumerate(colonnes):
        virgule = "," if i < len(colonnes) - 1 else ""
        lignes.append(f"    {colonne['colonne']} text{virgule}")
    lignes.append(");")
    return lignes


def rendre_commentaires(table: str, colonnes: list[dict]) -> list[str]:
    lignes = []
    for colonne in colonnes:
        libelle = echapper_sql(colonne["libelle_hosix"])
        litteral = (
            f"provenance={colonne['provenance']}; "
            f"preuve={colonne['preuve']}; "
            f"type_metier={colonne['type_metier']}; "
            f"libelle={libelle}"
        )
        lignes.append(f"comment on column {table}.{colonne['colonne']} is")
        lignes.append(f"'{litteral}';")
    return lignes


def nom_fichier_table(rang: int, table: str) -> str:
    slug = table.removeprefix("source.")
    return f"{rang:02d}_{slug}.sql"


def generer(racine: Path = RACINE) -> None:
    with REGISTRE.open(encoding="utf-8") as f:
        entrees = yaml.safe_load(f)

    tables = grouper_par_table(entrees)

    dossier_ddl = racine / "ingestion" / "ddl"
    dossier_ddl.mkdir(parents=True, exist_ok=True)

    lignes_schema = [ENTETE_SCHEMA.rstrip("\n"), "", "create schema if not exists source;"]
    (dossier_ddl / "00_schema_source.sql").write_text(
        "\n".join(lignes_schema).rstrip("\n") + "\n", encoding="utf-8"
    )

    for rang, (table, colonnes) in enumerate(tables.items(), start=1):
        lignes = [ENTETE_TABLE.rstrip("\n"), ""]
        lignes.extend(rendre_creation(table, colonnes))
        lignes.append("")
        lignes.extend(rendre_commentaires(table, colonnes))
        chemin = dossier_ddl / nom_fichier_table(rang, table)
        chemin.write_text("\n".join(lignes).rstrip("\n") + "\n", encoding="utf-8")


if __name__ == "__main__":
    generer()
