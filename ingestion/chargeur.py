"""Chargeur d'une partition vers PostgreSQL, avec quarantaine des lignes rejetées.

Pour chaque fichier (table, date de partition), lit le CSV, applique les contrôles
d'`ingestion/controles.py` plus le contrôle de cohérence de partition propre à ce module,
puis, si le taux de rejet reste sous le seuil déclaré, remplace le contenu de cette
partition dans une transaction unique : `DELETE` des deux schémas pour cette date, puis
insertion des lignes acceptées dans `source` et des lignes rejetées dans `quarantaine`. Le
`DELETE` rend le chargement idempotent — recharger le même fichier ou un fichier corrigé
remplace exactement le contenu précédent de cette partition, jamais ne l'accumule.

N'importe rien de `generator/` : la connexion et le registre viennent, comme le reste de
`ingestion/`, du dépôt et de l'environnement seuls.
"""

import argparse
import csv
import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from ingestion import controles

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

_FORMAT_DATE = "%m/%d/%Y"


def _charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def connexion() -> psycopg.Connection:
    variables = _charger_module(APPLIQUER_DDL).charger_environnement()
    return psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables.get("POSTGRES_PASSWORD", ""),
    )


def _colonnes_attendues(table: str) -> list[str]:
    registre = controles.charger_registre()
    return [e["colonne"] for e in registre if e["table"] == f"source.{table}"]


def _tables() -> list[str]:
    registre = controles.charger_registre()
    tables: list[str] = []
    for entree in registre:
        nom = entree["table"].removeprefix("source.")
        if nom not in tables:
            tables.append(nom)
    return tables


_SEUIL_QUARANTAINE = controles.charger_config()["seuil_quarantaine"]["valeur"]
_COLONNES_TECHNIQUES = ["rejet_motifs", "rejet_date_chargement", "rejet_partition"]


def _lire_lignes(chemin_csv: Path) -> tuple[list[str] | None, list[dict[str, str]]]:
    with chemin_csv.open(newline="", encoding="utf-8") as f:
        lecteur = csv.DictReader(f)
        entetes = lecteur.fieldnames
        lignes = list(lecteur)
    return (list(entetes) if entetes is not None else None), lignes


def _motifs_ligne(table: str, ligne: dict[str, str], date_attendue: str) -> list[str]:
    motifs = controles.controler_ligne(table, ligne)
    valeur_extraction = ligne.get("date_extraction", "")
    if valeur_extraction != "" and valeur_extraction != date_attendue:
        motifs.append(f"partition_incoherente:date_extraction:{valeur_extraction}")
    return motifs


def _inserer_source(
    curseur: psycopg.Cursor, table: str, colonnes: list[str], lignes: list[dict[str, str]]
) -> None:
    if not lignes:
        return
    liste_colonnes = ", ".join(colonnes)
    espaces_reserves = ", ".join(["%s"] * len(colonnes))
    requete = f"insert into source.{table} ({liste_colonnes}) values ({espaces_reserves})"
    parametres = [tuple(ligne.get(c, "") for c in colonnes) for ligne in lignes]
    curseur.executemany(requete, parametres)


def _inserer_quarantaine(
    curseur: psycopg.Cursor,
    table: str,
    colonnes: list[str],
    lignes: list[dict[str, str]],
    motifs_par_ligne: list[list[str]],
    date_iso: str,
) -> None:
    if not lignes:
        return
    maintenant = datetime.now(UTC)
    toutes_colonnes = colonnes + _COLONNES_TECHNIQUES
    liste_colonnes = ", ".join(toutes_colonnes)
    espaces_reserves = ", ".join(["%s"] * len(toutes_colonnes))
    requete = f"insert into quarantaine.{table} ({liste_colonnes}) values ({espaces_reserves})"
    parametres = [
        tuple(ligne.get(c, "") for c in colonnes) + (";".join(motifs), maintenant, date_iso)
        for ligne, motifs in zip(lignes, motifs_par_ligne, strict=True)
    ]
    curseur.executemany(requete, parametres)


def charger_table_partition(table: str, date_iso: str, chemin_csv: Path) -> dict:
    """Charge un fichier CSV d'une table pour une date de partition (ISO `AAAA-MM-JJ`).

    Renvoie un dict : `table`, `date`, `etat` (`charge`, `bloque_seuil`, `en_tete_invalide`),
    `lues`, `inserees`, `rejetees`.
    """
    colonnes = _colonnes_attendues(table)
    date_attendue = datetime.strptime(date_iso, "%Y-%m-%d").strftime(_FORMAT_DATE)

    entetes, lignes = _lire_lignes(chemin_csv)
    if entetes != colonnes:
        return {
            "table": table,
            "date": date_iso,
            "etat": "en_tete_invalide",
            "lues": 0,
            "inserees": 0,
            "rejetees": 0,
        }

    lues = len(lignes)
    motifs_par_ligne = [_motifs_ligne(table, ligne, date_attendue) for ligne in lignes]

    lignes_unicite_motifs = controles.controler_unicite(table, lignes)
    for i, motifs_unicite in enumerate(lignes_unicite_motifs):
        motifs_par_ligne[i].extend(motifs_unicite)

    rejetees = sum(1 for motifs in motifs_par_ligne if motifs)

    if lues > 0 and rejetees / lues > _SEUIL_QUARANTAINE:
        return {
            "table": table,
            "date": date_iso,
            "etat": "bloque_seuil",
            "lues": lues,
            "inserees": 0,
            "rejetees": rejetees,
        }

    lignes_acceptees = [
        ligne for ligne, motifs in zip(lignes, motifs_par_ligne, strict=True) if not motifs
    ]
    lignes_rejetees = [
        ligne for ligne, motifs in zip(lignes, motifs_par_ligne, strict=True) if motifs
    ]
    motifs_rejetees = [motifs for motifs in motifs_par_ligne if motifs]

    with connexion() as conn, conn.cursor() as curseur:
        curseur.execute(f"delete from source.{table} where date_extraction = %s", (date_attendue,))
        curseur.execute(f"delete from quarantaine.{table} where rejet_partition = %s", (date_iso,))
        _inserer_source(curseur, table, colonnes, lignes_acceptees)
        _inserer_quarantaine(curseur, table, colonnes, lignes_rejetees, motifs_rejetees, date_iso)

    return {
        "table": table,
        "date": date_iso,
        "etat": "charge",
        "lues": lues,
        "inserees": len(lignes_acceptees),
        "rejetees": rejetees,
    }


def charger_partition(date_iso: str, dossier: Path) -> dict[str, dict]:
    """Charge les tables du registre présentes pour une date de partition.

    Cherche `dossier/<table>.csv` pour chacune des tables du registre ; une table dont le
    fichier n'existe pas ce jour-là est ignorée sans erreur.
    """
    resultats: dict[str, dict] = {}
    for table in _tables():
        chemin = dossier / f"{table}.csv"
        if not chemin.exists():
            continue
        resultats[table] = charger_table_partition(table, date_iso, chemin)
    return resultats


def _dates_partition(dossier_table: Path) -> list[str]:
    return sorted(p.name for p in dossier_table.iterdir() if p.is_dir())


def _agregat_initial() -> dict:
    return {
        "lues": 0,
        "inserees": 0,
        "rejetees": 0,
        "charge": 0,
        "bloque_seuil": 0,
        "en_tete_invalide": 0,
    }


def charger_scenario(
    racine: Path,
    tables: list[str] | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
) -> dict[str, dict]:
    """Charge un scénario complet, arborescence `<racine>/source.<table>/<date ISO>/<table>.csv`.

    Parcourt les tables du registre (filtrées par `tables` si fourni, sinon toutes) puis
    leurs partitions en ordre chronologique (tri lexicographique des noms de répertoire
    `AAAA-MM-JJ`, qui coïncide avec l'ordre chronologique), et agrège les résultats par
    table : `lues`, `inserees`, `rejetees`, et le décompte de fichiers par état (`charge`,
    `bloque_seuil`, `en_tete_invalide`). Une table sans répertoire, ou une date sans
    fichier pour une table, est ignorée sans erreur.
    """
    tables_a_charger = tables if tables is not None else _tables()
    agregats: dict[str, dict] = {}

    for table in tables_a_charger:
        dossier_table = racine / f"source.{table}"
        if not dossier_table.exists():
            continue

        for date_iso in _dates_partition(dossier_table):
            if date_debut is not None and date_iso < date_debut:
                continue
            if date_fin is not None and date_iso > date_fin:
                continue

            chemin_csv = dossier_table / date_iso / f"{table}.csv"
            if not chemin_csv.exists():
                continue

            resultat = charger_table_partition(table, date_iso, chemin_csv)
            agregat = agregats.setdefault(table, _agregat_initial())
            agregat["lues"] += resultat["lues"]
            agregat["inserees"] += resultat["inserees"]
            agregat["rejetees"] += resultat["rejetees"]
            agregat[resultat["etat"]] += 1

    return agregats


def main(argv: list[str] | None = None) -> None:
    analyseur = argparse.ArgumentParser(
        description=(
            "Charge un scénario complet (arborescence source.<table>/<date>/<table>.csv) "
            "dans PostgreSQL."
        )
    )
    analyseur.add_argument(
        "racine", type=Path, help="Racine du scénario, contenant les répertoires source.<table>/"
    )
    analyseur.add_argument(
        "--table",
        action="append",
        dest="tables",
        metavar="TABLE",
        help="Limiter le chargement à cette table (répétable ; toutes les tables par défaut)",
    )
    analyseur.add_argument(
        "--date-debut", metavar="AAAA-MM-JJ", help="Date de partition minimale, incluse"
    )
    analyseur.add_argument(
        "--date-fin", metavar="AAAA-MM-JJ", help="Date de partition maximale, incluse"
    )
    arguments = analyseur.parse_args(argv)

    agregats = charger_scenario(
        arguments.racine, arguments.tables, arguments.date_debut, arguments.date_fin
    )
    for table in sorted(agregats):
        print(f"{table}: {agregats[table]}")


if __name__ == "__main__":
    main()
