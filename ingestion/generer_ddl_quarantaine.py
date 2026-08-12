"""Rend docs/champs/registre_champs.yml en DDL du schéma quarantaine, un fichier par table.

Réutilise le mécanisme de lecture et de groupement du registre de
`docs/champs/generer_ddl.py`, chargé dynamiquement en lecture seule : ce fichier n'est ni
importé comme paquet ni modifié, seulement exécuté pour obtenir les mêmes structures que le
DDL source à partir du même registre. Chaque table `quarantaine.<table>` reprend les
colonnes de `source.<table>` dans le même ordre, toutes en `text`, sans contrainte, puis
trois colonnes techniques (`rejet_motifs`, `rejet_date_chargement`, `rejet_partition`) hors
registre : elles ne portent pas de commentaire de provenance, la couverture bidirectionnelle
de `tests/test_provenance.py` ne porte que sur les schémas source/intermediate/marts.
"""

import importlib.util
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
GENERER_DDL_SOURCE = RACINE / "docs" / "champs" / "generer_ddl.py"

RANG_SCHEMA = 21
RANG_PREMIERE_TABLE = 22

ENTETE = """\
-- Fichier produit mécaniquement depuis le registre des champs : ne pas
-- modifier à la main.
"""

COLONNES_TECHNIQUES = [
    ("rejet_motifs", "text"),
    ("rejet_date_chargement", "timestamptz"),
    ("rejet_partition", "text"),
]


def charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rendre_creation(table_quarantaine: str, colonnes_source: list[dict]) -> list[str]:
    lignes = [
        f"drop table if exists {table_quarantaine} cascade;",
        f"create table {table_quarantaine} (",
    ]
    total = len(colonnes_source) + len(COLONNES_TECHNIQUES)
    i = 0
    for colonne in colonnes_source:
        i += 1
        virgule = "," if i < total else ""
        lignes.append(f"    {colonne['colonne']} text{virgule}")
    for nom, type_sql in COLONNES_TECHNIQUES:
        i += 1
        virgule = "," if i < total else ""
        lignes.append(f"    {nom} {type_sql}{virgule}")
    lignes.append(");")
    return lignes


def nom_fichier_table(rang: int, table_source: str) -> str:
    slug = table_source.removeprefix("source.")
    return f"{rang:02d}_quarantaine_{slug}.sql"


def generer(racine: Path = RACINE) -> None:
    generer_ddl_source = charger_module(GENERER_DDL_SOURCE)
    with generer_ddl_source.REGISTRE.open(encoding="utf-8") as f:
        entrees = yaml.safe_load(f)
    tables = generer_ddl_source.grouper_par_table(entrees)

    dossier_ddl = racine / "ingestion" / "ddl"
    dossier_ddl.mkdir(parents=True, exist_ok=True)

    lignes_schema = [ENTETE.rstrip("\n"), "", "create schema if not exists quarantaine;"]
    (dossier_ddl / f"{RANG_SCHEMA:02d}_schema_quarantaine.sql").write_text(
        "\n".join(lignes_schema).rstrip("\n") + "\n", encoding="utf-8"
    )

    for decalage, (table_source, colonnes_source) in enumerate(tables.items()):
        rang = RANG_PREMIERE_TABLE + decalage
        table_quarantaine = "quarantaine." + table_source.removeprefix("source.")
        lignes = [ENTETE.rstrip("\n"), ""]
        lignes.extend(rendre_creation(table_quarantaine, colonnes_source))
        chemin = dossier_ddl / nom_fichier_table(rang, table_source)
        chemin.write_text("\n".join(lignes).rstrip("\n") + "\n", encoding="utf-8")


if __name__ == "__main__":
    generer()
