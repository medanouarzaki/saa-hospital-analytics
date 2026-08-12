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
