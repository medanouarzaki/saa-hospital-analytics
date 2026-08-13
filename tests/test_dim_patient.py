"""Confrontation de marts.dim_patient (SCD 2) à la vérité terrain du générateur.

Deux propriétés, démontrées par script au lot précédent, committées ici : l'égalité d'ensembles
entre les n_ipp à changement métier réel dans dim_patient et les n_ipp de fiches_modifiees hors
quarantaine ; l'exactitude version par version (valeurs avant/après, bornes de validité) pour
chaque entrée hors quarantaine. Les colonnes métier modifiables viennent de
generator.patients.COLONNES_PAR_TYPE_MODIFICATION, importées directement — jamais recopiées.

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


def test_egalite_ensembles_fiches_modifiees() -> None:
    with _connexion() as conn:
        a = _ensemble_a_changements_reels(conn)
        en_quarantaine = _n_ipp_en_quarantaine(conn)

    entrees = _charger_entrees_fiches_modifiees()
    b = {e["n_ipp"] for e in entrees if e["n_ipp"] not in en_quarantaine}

    manquants_a_b = sorted(a - b)
    manquants_a_a = sorted(b - a)
    assert not manquants_a_b and not manquants_a_a, (
        f"n_ipp de dim_patient absents de fiches_modifiees : {manquants_a_b} ; "
        f"n_ipp de fiches_modifiees absents de dim_patient : {manquants_a_a}"
    )


def test_exactitude_des_versions() -> None:
    with _connexion() as conn:
        en_quarantaine = _n_ipp_en_quarantaine(conn)
        entrees = [
            e for e in _charger_entrees_fiches_modifiees() if e["n_ipp"] not in en_quarantaine
        ]
        if not entrees:
            pytest.fail("aucune entrée de fiches_modifiees hors quarantaine : rien à confronter")

        ipps = sorted({e["n_ipp"] for e in entrees})
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

    index_colonne = {nom: 4 + i for i, nom in enumerate(COLONNES_MODIFIABLES)}
    par_ipp: dict[str, list[tuple]] = {}
    for ligne in lignes:
        par_ipp.setdefault(ligne[0], []).append(ligne)

    non_conformes: list[tuple[str, str]] = []
    for entree in entrees:
        versions = par_ipp.get(entree["n_ipp"])
        if not versions or len(versions) != 2:
            non_conformes.append((entree["n_ipp"], "nombre de versions != 2"))
            continue

        ancienne, nouvelle = versions
        date_attendue = datetime.strptime(entree["date_extraction"], "%m/%d/%Y").date()

        conforme = ancienne[3] is False and nouvelle[3] is True
        conforme = conforme and ancienne[2] == date_attendue and nouvelle[1] == date_attendue
        for colonne, valeurs in entree["colonnes"].items():
            idx = index_colonne[colonne]
            conforme = (
                conforme and ancienne[idx] == valeurs["avant"] and nouvelle[idx] == valeurs["apres"]
            )

        if conforme:
            continue
        non_conformes.append((entree["n_ipp"], "valeurs ou dates non conformes"))

    assert not non_conformes, (
        f"{len(non_conformes)} entrée(s) non conforme(s) sur {len(entrees)} : {non_conformes[:20]}"
    )
