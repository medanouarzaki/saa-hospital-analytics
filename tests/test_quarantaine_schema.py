"""Contrôle bloquant sur le schéma `quarantaine` : chaque table `quarantaine.<table>` doit
porter exactement les colonnes du registre pour `source.<table>`, dans le même ordre, suivies
des trois colonnes techniques de rejet.

Connexion à la base par les mêmes variables d'environnement que `tests/test_provenance.py` ;
si la base est injoignable, ce test échoue plutôt que d'être sauté — un test sauté est un
succès qui ne mesure rien.
"""

import importlib.util
from pathlib import Path

import psycopg
import yaml

RACINE = Path(__file__).resolve().parent.parent
REGISTRE = RACINE / "docs" / "champs" / "registre_champs.yml"
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

COLONNES_TECHNIQUES = ["rejet_motifs", "rejet_date_chargement", "rejet_partition"]


def charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def connexion() -> psycopg.Connection:
    variables = charger_module(APPLIQUER_DDL).charger_environnement()
    return psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables["POSTGRES_PASSWORD"],
        connect_timeout=5,
    )


def colonnes_attendues_par_table() -> dict[str, list[str]]:
    with REGISTRE.open(encoding="utf-8") as f:
        registre = yaml.safe_load(f)

    par_table: dict[str, list[str]] = {}
    for entree in registre:
        table = entree["table"].removeprefix("source.")
        par_table.setdefault(table, []).append(entree["colonne"])

    return {table: colonnes + COLONNES_TECHNIQUES for table, colonnes in par_table.items()}


def colonnes_catalogue_par_table() -> dict[str, list[str]]:
    with connexion() as conn:
        lignes = conn.execute(
            """
            select c.table_name, c.column_name
            from information_schema.columns c
            where c.table_schema = 'quarantaine'
            order by c.table_name, c.ordinal_position
            """
        ).fetchall()

    par_table: dict[str, list[str]] = {}
    for table, colonne in lignes:
        par_table.setdefault(table, []).append(colonne)
    return par_table


def test_tables_quarantaine_colonnes_conformes_au_registre() -> None:
    attendues = colonnes_attendues_par_table()
    catalogue = colonnes_catalogue_par_table()

    tables_manquantes = set(attendues) - set(catalogue)
    tables_en_trop = set(catalogue) - set(attendues)

    assert not tables_manquantes, (
        f"tables du registre absentes du schéma quarantaine : {sorted(tables_manquantes)}"
    )
    assert not tables_en_trop, (
        f"tables du schéma quarantaine absentes du registre : {sorted(tables_en_trop)}"
    )

    echecs = []
    for table in sorted(attendues):
        colonnes_attendues = attendues[table]
        colonnes_reelles = catalogue[table]

        manquantes = [c for c in colonnes_attendues if c not in colonnes_reelles]
        en_trop = [c for c in colonnes_reelles if c not in colonnes_attendues]
        if manquantes or en_trop:
            echecs.append(f"quarantaine.{table} : manquantes={manquantes} en_trop={en_trop}")
            continue

        if colonnes_reelles != colonnes_attendues:
            echecs.append(
                f"quarantaine.{table} : ordre différent — "
                f"attendu={colonnes_attendues} réel={colonnes_reelles}"
            )

    assert not echecs, "\n".join(echecs)
