"""Confrontation de marts.dim_patient (SCD 2) à la vérité terrain du générateur.

Comptable des retraits légitimes de la chaîne de chargement : chaque entrée de fiches_modifiees
est SOIT pleinement matérialisée (paire SCD 2 exacte : valeurs avant/après, bornes de validité
alignées sur la date_extraction enregistrée), SOIT expliquée par une preuve mesurée en base —
(i) le n_ipp présent dans quarantaine.patients, ou (ii) la partition de la version manquante
entièrement absente de source.patients (zéro ligne pour cette date_extraction) alors que le CSV
brut du scénario, pour cette même partition, n'est pas vide (le blocage en bloc du chargeur,
ingestion/chargeur.py::charger_table_partition, état bloque_seuil, est le seul mécanisme qui
produit cet état sur une partition non vide au départ). Une version manquante sans l'une de ces
deux preuves reste un échec réel, jamais excusé silencieusement.

Les colonnes métier modifiables viennent de generator.patients.COLONNES_PAR_TYPE_MODIFICATION,
importées directement — jamais recopiées.

Exige une base avec dbt exécuté (marts.dim_patient) ; ne s'exécute utilement que dans le job CI
dédié ou contre une base Compose locale déjà chargée et dbt-runnée. Chemin de la vérité terrain
et connexion base paramétrables par variable d'environnement, pour pointer sur un sous-ensemble
généré en CI. Aucun skip silencieux : base ou fichier manquants font échouer le test.
"""

import importlib.util
import os
from datetime import datetime
from pathlib import Path

import psycopg
import pytest
import yaml

from generator.patients import COLONNES_PAR_TYPE_MODIFICATION

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"
VERITE_TERRAIN_DEFAUT = RACINE / "generator" / "output" / "scenario_30" / "verite_terrain.yml"

COLONNES_MODIFIABLES = sorted(
    {colonne for colonnes in COLONNES_PAR_TYPE_MODIFICATION.values() for colonne in colonnes}
)
INDEX_COLONNE = {nom: 4 + i for i, nom in enumerate(COLONNES_MODIFIABLES)}


def _charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _connexion() -> psycopg.Connection:
    variables = _charger_module(APPLIQUER_DDL).charger_environnement()
    try:
        return psycopg.connect(
            host=variables["POSTGRES_HOST"],
            port=variables["POSTGRES_PORT"],
            dbname=variables["POSTGRES_DB"],
            user=variables["POSTGRES_USER"],
            password=variables.get("POSTGRES_PASSWORD", ""),
        )
    except psycopg.OperationalError as exc:
        pytest.fail(
            f"connexion impossible à la base ({exc}) : marts.dim_patient doit être chargée "
            "et dbt exécuté avant ce test"
        )


def _chemin_verite_terrain() -> Path:
    chemin = Path(os.environ.get("VERITE_TERRAIN_PATIENTS", str(VERITE_TERRAIN_DEFAUT)))
    if not chemin.exists():
        pytest.fail(f"{chemin} : fichier de vérité terrain introuvable")
    return chemin


def _charger_entrees_fiches_modifiees() -> list[dict]:
    with _chemin_verite_terrain().open(encoding="utf-8") as f:
        verite = yaml.safe_load(f)
    return verite["fiches_modifiees"]["entrees"]


def _n_ipp_en_quarantaine(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("select distinct n_ipp from quarantaine.patients")
        return {ligne[0] for ligne in cur.fetchall()}


def _ensemble_a_changements_reels(conn: psycopg.Connection) -> set[str]:
    condition = " or ".join(f"a.{c} is distinct from b.{c}" for c in COLONNES_MODIFIABLES)
    requete = f"""
        with deux_versions as (
            select n_ipp from marts.dim_patient group by n_ipp having count(*) = 2
        )
        select a.n_ipp
        from marts.dim_patient a
        join marts.dim_patient b on a.n_ipp = b.n_ipp and a.valide_de < b.valide_de
        where a.n_ipp in (select n_ipp from deux_versions)
          and ({condition})
    """
    with conn.cursor() as cur:
        cur.execute(requete)
        return {ligne[0] for ligne in cur.fetchall()}


def _versions_par_ipp(conn: psycopg.Connection, ipps: list[str]) -> dict[str, list[tuple]]:
    if not ipps:
        return {}
    colonnes_select = [
        "n_ipp",
        "valide_de",
        "valide_jusqu_a",
        "est_courante",
        *COLONNES_MODIFIABLES,
    ]
    with conn.cursor() as cur:
        cur.execute(
            f"select {', '.join(colonnes_select)} from marts.dim_patient "
            "where n_ipp = any(%s) order by n_ipp, valide_de",
            (ipps,),
        )
        lignes = cur.fetchall()
    par_ipp: dict[str, list[tuple]] = {}
    for ligne in lignes:
        par_ipp.setdefault(ligne[0], []).append(ligne)
    return par_ipp


def _partition_source_non_vide_au_depart(racine_scenario: Path, date_iso: str) -> bool:
    chemin_csv = racine_scenario / "source.patients" / date_iso / "patients.csv"
    if not chemin_csv.exists():
        return False
    with chemin_csv.open(encoding="utf-8") as f:
        n_lignes = sum(1 for _ in f) - 1  # moins l'en-tete
    return n_lignes > 0


def _partition_absente_de_la_base(conn: psycopg.Connection, date_source: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "select count(*) from source.patients where date_extraction = %s", (date_source,)
        )
        return cur.fetchone()[0] == 0


def _conforme(versions: list[tuple], entree: dict, date_attendue) -> bool:
    ancienne, nouvelle = versions
    conforme = ancienne[3] is False and nouvelle[3] is True
    conforme = conforme and ancienne[2] == date_attendue and nouvelle[1] == date_attendue
    for colonne, valeurs in entree["colonnes"].items():
        idx = INDEX_COLONNE[colonne]
        conforme = (
            conforme and ancienne[idx] == valeurs["avant"] and nouvelle[idx] == valeurs["apres"]
        )
    return conforme


def _classer_entrees(
    conn: psycopg.Connection, entrees: list[dict], racine_scenario: Path
) -> tuple[list[str], list[str], list[tuple[str, str]], list[tuple[str, str]]]:
    en_quarantaine = _n_ipp_en_quarantaine(conn)
    ipps = sorted({e["n_ipp"] for e in entrees})
    par_ipp = _versions_par_ipp(conn, ipps)

    conformes: list[str] = []
    exclues_quarantaine: list[str] = []
    exclues_partition: list[tuple[str, str]] = []
    non_conformes: list[tuple[str, str]] = []

    for entree in entrees:
        n_ipp = entree["n_ipp"]
        versions = par_ipp.get(n_ipp, [])
        date_attendue = datetime.strptime(entree["date_extraction"], "%m/%d/%Y").date()

        if len(versions) == 2:
            if _conforme(versions, entree, date_attendue):
                conformes.append(n_ipp)
            else:
                non_conformes.append((n_ipp, "deux versions présentes mais non conformes"))
            continue

        if n_ipp in en_quarantaine:
            exclues_quarantaine.append(n_ipp)
            continue

        date_source = date_attendue.strftime("%m/%d/%Y")
        partition_absente = _partition_absente_de_la_base(conn, date_source)
        partition_non_vide_au_depart = _partition_source_non_vide_au_depart(
            racine_scenario, date_attendue.isoformat()
        )
        if partition_absente and partition_non_vide_au_depart:
            exclues_partition.append((n_ipp, date_source))
        else:
            raison = f"{len(versions)} version(s), aucune preuve d'exclusion prouvée"
            non_conformes.append((n_ipp, raison))

    return conformes, exclues_quarantaine, exclues_partition, non_conformes


def test_egalite_ensembles_fiches_modifiees() -> None:
    entrees = _charger_entrees_fiches_modifiees()
    racine_scenario = _chemin_verite_terrain().parent

    with _connexion() as conn:
        a = _ensemble_a_changements_reels(conn)
        _conformes, exclues_quarantaine, exclues_partition, non_conformes = _classer_entrees(
            conn, entrees, racine_scenario
        )

    exclues = set(exclues_quarantaine) | {n for n, _ in exclues_partition}
    b = {e["n_ipp"] for e in entrees} - exclues

    manquants_a_b = sorted(a - b)
    manquants_a_a = sorted(b - a)
    assert not manquants_a_b and not manquants_a_a, (
        f"n_ipp à changement métier réel absents des entrées non-excusées : {manquants_a_b} ; "
        f"entrées non-excusées absentes des paires à changement métier réel : {manquants_a_a} ; "
        f"non conformes : {non_conformes}"
    )


def test_exactitude_des_versions() -> None:
    entrees = _charger_entrees_fiches_modifiees()
    racine_scenario = _chemin_verite_terrain().parent
    if not entrees:
        pytest.fail("aucune entrée de fiches_modifiees : rien à confronter")

    with _connexion() as conn:
        conformes, exclues_quarantaine, exclues_partition, non_conformes = _classer_entrees(
            conn, entrees, racine_scenario
        )

    total = len(entrees)
    somme_expliquee = len(conformes) + len(exclues_quarantaine) + len(exclues_partition)
    assert total == somme_expliquee, (
        f"total={total} conformes={len(conformes)} exclues_quarantaine={len(exclues_quarantaine)} "
        f"exclues_partition={len(exclues_partition)} (={somme_expliquee}) "
        f"non_conformes={len(non_conformes)} : {non_conformes[:20]}"
    )
