"""Idempotence de la chaîne : le chargement d'une date d'extraction fait le travail, et le
refaire ne change rien.

Ce test DÉTRUIT puis RECHARGE des partitions de données. Il n'a le droit de s'exécuter que
contre une cible que l'appelant a explicitement déclarée jetable — l'incident du bloc a montré
qu'aucun mécanisme du dépôt ne distingue par lui-même une base réelle d'une base jetable à
partir de ses seuls paramètres de connexion. `SAA_INSTRUMENT_JETABLE` (valeur `"1"`) est cette
déclaration ; son absence fait échouer le test bruyamment, jamais silencieusement.

Toute propriété vérifiée ici est une égalité entre deux mesures prises par les mêmes fonctions
à deux instants — jamais une valeur de volumétrie écrite d'avance. La colonne
`rejet_date_chargement` de la quarantaine (horodatage réel du chargement, pas une donnée
métier) est exclue de toute empreinte de contenu ; le test lui-même le prouve avant de s'en
servir : l'inclure ferait échouer une comparaison entre deux états par ailleurs identiques.

Chaque test établit lui-même ses préconditions : la base de métadonnées de l'orchestrateur
(`preparer_orchestrateur`) et, dans `tests/test_rattrapage.py`, les journées qu'il traite —
jamais héritées d'un autre fichier de test ni d'une préparation externe au fichier de workflow.

`tests/test_rattrapage.py` importe les fonctions utilitaires ci-dessous (aucune n'est préfixée
`test_`, aucune n'est donc collectée comme test par elle-même).
"""

import os
import subprocess
import sys
from pathlib import Path

import psycopg2
import pytest

RACINE = Path(__file__).resolve().parent.parent
GRAPHE = RACINE / "airflow" / "saa_daily.py"

TABLES_SOURCE = (
    "creances",
    "encaissements",
    "factures",
    "lignes_facture",
    "mouvements",
    "passages",
    "passages_urgences",
    "patients",
    "prises_en_charge",
    "relances",
    "rendez_vous",
)

COLONNE_HORODATAGE_QUARANTAINE = "rejet_date_chargement"


def verifier_base_jetable() -> None:
    if os.environ.get("SAA_INSTRUMENT_JETABLE") != "1":
        pytest.fail(
            "SAA_INSTRUMENT_JETABLE doit valoir '1' pour exécuter ce test : il détruit et "
            "recharge des partitions de données. Ce n'est jamais un skip silencieux — la "
            "variable atteste explicitement que la cible visée est jetable."
        )


def preparer_orchestrateur() -> None:
    """Établit la base de métadonnées de l'orchestrateur dont `executer_graphe()` a besoin —
    évaluée ici, à l'exécution du test, jamais au niveau du module. `executer_graphe()` lance
    `airflow dags test` en sous-processus, qui hérite silencieusement de l'environnement du
    processus appelant ; sans cette préparation, un `AIRFLOW_HOME` neuf ferait échouer ce
    sous-processus (base de métadonnées non migrée), et un `AIRFLOW_HOME` absent ferait
    retomber l'orchestrateur sur le répertoire personnel de l'utilisateur — les deux cas
    échouent ici bruyamment plutôt que d'être découverts plus tard dans un sous-processus."""
    airflow_home = os.environ.get("AIRFLOW_HOME")
    if not airflow_home:
        pytest.fail(
            "AIRFLOW_HOME doit être défini pour exécuter ce test : sans cette variable, "
            "l'orchestrateur retombe silencieusement sur le répertoire personnel de "
            "l'utilisateur (~/airflow)."
        )
    airflow_home_reel = Path(airflow_home).resolve()
    if airflow_home_reel == RACINE or RACINE in airflow_home_reel.parents:
        pytest.fail(
            f"AIRFLOW_HOME ({airflow_home_reel}) désigne un emplacement à l'intérieur du "
            f"dépôt ({RACINE}) : la base de métadonnées de l'orchestrateur ne doit jamais y "
            "être écrite."
        )
    resultat = subprocess.run(
        ["uv", "run", "airflow", "db", "migrate"],
        cwd=RACINE,
        capture_output=True,
        text=True,
    )
    assert resultat.returncode == 0, (
        "la préparation de la base de métadonnées de l'orchestrateur a échoué (code "
        f"{resultat.returncode}) :\n{resultat.stdout[-4000:]}\n{resultat.stderr[-4000:]}"
    )


def connexion() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )


def _colonnes(cur, schema: str, table: str, exclure: tuple[str, ...] = ()) -> list[str]:
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
        (schema, table),
    )
    return [r[0] for r in cur.fetchall() if r[0] not in exclure]


def empreinte(
    cur, schema: str, table: str, where_col: str, where_val: str, exclure: tuple[str, ...] = ()
) -> tuple[int, str]:
    """Décompte et somme de contrôle du contenu, trié, d'une table filtrée sur une colonne.

    `exclure` retire des colonnes nommées de la comparaison (l'horodatage de chargement de la
    quarantaine, notamment) avant de calculer l'empreinte.
    """
    cols = _colonnes(cur, schema, table, exclure)
    cols_sql = ", ".join(f'"{c}"' for c in cols)
    requete = (
        f"SELECT count(*), md5(coalesce(string_agg(t::text, '' ORDER BY t::text), '')) "
        f'FROM (SELECT {cols_sql} FROM "{schema}"."{table}" WHERE "{where_col}" = %s) t'
    )
    cur.execute(requete, (where_val,))
    return cur.fetchone()


def empreinte_n_ipp(cur, schema: str, table: str, colonne_n_ipp: str, n_ipps: list[str]):
    """Empreinte d'une table filtrée à un ensemble de n_ipp donné, sur une seule colonne
    d'identité (dim_patient, grappes_identite)."""
    cols = _colonnes(cur, schema, table)
    cols_sql = ", ".join(f'"{c}"' for c in cols)
    requete = (
        f"SELECT count(*), md5(coalesce(string_agg(t::text, '' ORDER BY t::text), '')) "
        f'FROM (SELECT {cols_sql} FROM "{schema}"."{table}" WHERE "{colonne_n_ipp}" = ANY(%s)) t'
    )
    cur.execute(requete, (n_ipps,))
    return cur.fetchone()


def empreinte_paires_n_ipp(cur, n_ipps: list[str]):
    """`linkage.paires_candidates` n'a pas une seule colonne d'identité : une paire touche
    l'ensemble dès que l'un de ses deux membres y figure."""
    cols = _colonnes(cur, "linkage", "paires_candidates")
    cols_sql = ", ".join(f'"{c}"' for c in cols)
    cur.execute(
        f"SELECT count(*), md5(coalesce(string_agg(t::text, '' ORDER BY t::text), '')) "
        f"FROM (SELECT {cols_sql} FROM linkage.paires_candidates "
        f"WHERE n_ipp_1 = ANY(%s) OR n_ipp_2 = ANY(%s)) t",
        (n_ipps, n_ipps),
    )
    return cur.fetchone()


def n_ipps_de_la_partition(cur, date_extraction_us: str) -> list[str]:
    cur.execute(
        "SELECT n_ipp FROM source.patients WHERE date_extraction = %s ORDER BY n_ipp",
        (date_extraction_us,),
    )
    return [r[0] for r in cur.fetchall()]


def etat_partition(cur, date_extraction_us: str, date_extraction_iso: str) -> dict:
    """État de la journée dans `source.*`/`quarantaine.*` seuls — ce que le retrait direct en
    base et le rechargement affectent."""
    etat = {}
    for table in TABLES_SOURCE:
        etat[f"source.{table}"] = empreinte(
            cur, "source", table, "date_extraction", date_extraction_us
        )
        etat[f"quarantaine.{table}"] = empreinte(
            cur,
            "quarantaine",
            table,
            "rejet_partition",
            date_extraction_iso,
            exclure=(COLONNE_HORODATAGE_QUARANTAINE,),
        )
    return etat


def etat_population(cur, n_ipps: list[str]) -> dict:
    """État de la couche dimensionnelle et du rapprochement, restreint aux identités de la
    partition traitée — pas la totalité de la base, qui porte aussi d'autres journées déjà
    chargées sur le même instrument."""
    return {
        "marts.dim_patient": empreinte_n_ipp(cur, "marts", "dim_patient", "n_ipp", n_ipps),
        "linkage.paires_candidates": empreinte_paires_n_ipp(cur, n_ipps),
        "linkage.grappes_identite": empreinte_n_ipp(
            cur, "linkage", "grappes_identite", "n_ipp", n_ipps
        ),
    }


def retirer_partition(cur, date_extraction_us: str, date_extraction_iso: str) -> None:
    for table in TABLES_SOURCE:
        cur.execute(
            f'DELETE FROM source."{table}" WHERE date_extraction = %s', (date_extraction_us,)
        )
        cur.execute(
            f'DELETE FROM quarantaine."{table}" WHERE rejet_partition = %s', (date_extraction_iso,)
        )


def executer_graphe(date_logique: str) -> subprocess.CompletedProcess:
    resultat = subprocess.run(
        [
            "uv",
            "run",
            "airflow",
            "dags",
            "test",
            "saa_daily",
            date_logique,
            "-f",
            str(GRAPHE),
        ],
        cwd=RACINE,
        capture_output=True,
        text=True,
    )
    return resultat


def _date_us(date_iso: str) -> str:
    annee, mois, jour = date_iso.split("-")
    return f"{mois}/{jour}/{annee}"


def test_chargement_idempotent() -> None:
    verifier_base_jetable()
    preparer_orchestrateur()

    date_iso = "2024-02-08"
    date_us = _date_us(date_iso)

    with connexion() as conn, conn.cursor() as cur:
        n_ipps = n_ipps_de_la_partition(cur, date_us)
        assert n_ipps, (
            f"aucune fiche patient trouvée pour {date_iso} : ce test exige une date déjà "
            "chargée sur l'instrument"
        )

        # 1. État de référence : l'instrument est déjà en régime établi.
        reference_partition = etat_partition(cur, date_us, date_iso)
        reference_population = etat_population(cur, n_ipps)

        # Preuve que l'exclusion de l'horodatage n'est pas un confort : la même requête,
        # SANS l'exclure, doit différer de la version excluant l'horodatage (ci-dessus)
        # si la partition est rejouée entre-temps — vérifié au temps 4, ci-dessous.

        # 2. Retrait direct en base : l'état doit changer.
        retirer_partition(cur, date_us, date_iso)
        conn.commit()
        etat_apres_retrait = etat_partition(cur, date_us, date_iso)
        assert etat_apres_retrait != reference_partition, (
            "le retrait de la partition n'a rien changé à l'état mesuré : ce test ne "
            "mesurerait rien — la sélection de table/colonnes est probablement erronée"
        )
        for table in TABLES_SOURCE:
            assert etat_apres_retrait[f"source.{table}"][0] == 0
            assert etat_apres_retrait[f"quarantaine.{table}"][0] == 0

    # 3. Rejeu du graphe pour cette date logique : retour à l'état de référence.
    resultat = executer_graphe(date_iso)
    assert resultat.returncode == 0, (
        f"le graphe a échoué au rejeu (code {resultat.returncode}) :\n"
        f"{resultat.stdout[-4000:]}\n{resultat.stderr[-4000:]}"
    )

    with connexion() as conn, conn.cursor() as cur:
        etat_apres_rejeu = etat_partition(cur, date_us, date_iso)
        etat_apres_rejeu_avec_horodatage = {
            table: empreinte(cur, "quarantaine", table, "rejet_partition", date_iso)
            for table in TABLES_SOURCE
        }
        population_apres_rejeu = etat_population(cur, n_ipps)

    divergentes = [k for k in etat_apres_rejeu if etat_apres_rejeu[k] != reference_partition.get(k)]
    assert etat_apres_rejeu == reference_partition, (
        "l'état après rejeu du graphe diverge de l'état de référence (hors horodatage de "
        f"quarantaine), clés divergentes : {divergentes}"
    )
    assert population_apres_rejeu == reference_population, (
        "la couche dimensionnelle ou le rapprochement, restreints à cette population, "
        "divergent de l'état de référence après rejeu"
    )

    # 4. Second rejeu, sans rien changer : idempotence.
    resultat2 = executer_graphe(date_iso)
    assert resultat2.returncode == 0, (
        f"le second rejeu du graphe a échoué (code {resultat2.returncode}) :\n"
        f"{resultat2.stdout[-4000:]}\n{resultat2.stderr[-4000:]}"
    )

    with connexion() as conn, conn.cursor() as cur:
        etat_apres_second_rejeu = etat_partition(cur, date_us, date_iso)
        etat_apres_second_rejeu_avec_horodatage = {
            table: empreinte(cur, "quarantaine", table, "rejet_partition", date_iso)
            for table in TABLES_SOURCE
        }
        population_apres_second_rejeu = etat_population(cur, n_ipps)

    assert etat_apres_second_rejeu == etat_apres_rejeu, (
        "un second rejeu de la même journée change l'état mesuré (hors horodatage) : "
        "la chaîne n'est pas idempotente"
    )
    assert population_apres_second_rejeu == population_apres_rejeu

    # Preuve que l'exclusion de l'horodatage n'est pas un confort : SANS l'exclure, les
    # deux rejeux produisent des empreintes DIFFÉRENTES sur la quarantaine, alors que la
    # comparaison sans l'horodatage (ci-dessus) les trouve identiques.
    divergences_avec_horodatage = [
        table
        for table in TABLES_SOURCE
        if etat_apres_second_rejeu_avec_horodatage[table][0] > 0
        and etat_apres_second_rejeu_avec_horodatage[table]
        != etat_apres_rejeu_avec_horodatage[table]
    ]
    assert divergences_avec_horodatage, (
        "aucune table de quarantaine avec horodatage inclus n'a divergé entre les deux "
        "rejeux : l'exclusion de l'horodatage n'a pas été mise à l'épreuve sur ce jeu — "
        "choisir une date dont la quarantaine porte au moins une ligne"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
