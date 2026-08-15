"""Rattrapage : rejouer plusieurs jours d'extraction dans le désordre doit produire le même état
que les rejouer dans l'ordre chronologique.

Mêmes exigences de sécurité et mêmes conventions de mesure que `tests/test_idempotence.py`, dont
ce fichier importe les fonctions utilitaires plutôt que de les dupliquer : garde-fou
`SAA_INSTRUMENT_JETABLE`, empreintes de contenu excluant `rejet_date_chargement`, comparaisons
uniquement par égalité entre deux mesures.

L'intégrité référentielle vérifiée par `dbt_tests` (tâche du graphe) est une propriété de LA
BASE ENTIÈRE à l'instant du rejeu, pas une propriété du seul jour traité : le générateur produit
une continuité de facturation à travers le temps (un encaissement d'un jour peut régler une
facture émise un autre jour, mesuré : 33 rapprochements de ce type rien que sur les trois dates
de ce test). Retirer plusieurs journées à la fois et les recharger une par une laisse donc,
entre deux rejeux, un état transitoire où certaines des journées retirées manquent encore : `
dbt_tests` y échoue légitimement, sans que la tâche de chargement elle-même soit en cause. Ce
test ne l'ignore pas silencieusement : il exige, pour chaque rejeu intermédiaire, que la
partition de la journée traitée soit bien revenue (le chargement a fonctionné), et n'exige un
graphe intégralement vert (`dbt_tests` compris) qu'une fois les trois journées rechargées.

Un contrôle de sensibilité positif est inclus : l'état après deux jours chargés doit différer de
l'état après trois jours chargés, sur le même ensemble d'identités. Sans cette preuve, une
comparaison d'état qui aurait un trou (colonne oubliée, filtre trop large) pourrait toujours
réussir sans jamais rien vérifier.

Ce test charge lui-même les trois journées dont il a besoin (`_etablir_journees`), plutôt que
de supposer qu'un autre fichier de test les aurait déjà laissées en base — y compris lorsqu'il
est exécuté seul, dans une invocation qui n'a jamais fait tourner `test_idempotence.py`.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from ingestion import chargeur
from tests.test_idempotence import (
    TABLES_SOURCE,
    _date_us,
    connexion,
    etat_partition,
    etat_population,
    executer_graphe,
    n_ipps_de_la_partition,
    preparer_orchestrateur,
    retirer_partition,
    verifier_base_jetable,
)

RACINE = Path(__file__).resolve().parent.parent

DATES_CHRONOLOGIQUES = ("2024-01-20", "2024-02-08", "2024-03-05")
ORDRE_NON_CHRONOLOGIQUE = ("2024-03-05", "2024-01-20", "2024-02-08")

assert sorted(ORDRE_NON_CHRONOLOGIQUE) == sorted(DATES_CHRONOLOGIQUES)
assert ORDRE_NON_CHRONOLOGIQUE != DATES_CHRONOLOGIQUES


def _racine_scenario() -> Path:
    """Évaluée à l'appel, jamais à l'import : un scénario n'est pas garanti présent au seul
    chargement de ce module (par exemple à la collecte pytest)."""
    return Path(
        os.environ.get("SAA_SCENARIO_ROOT", str(RACINE / "generator" / "output" / "scenario_30"))
    )


def _etablir_journees() -> None:
    """Charge les trois journées dont ce test a besoin, sur les onze tables, depuis le
    sous-ensemble actif, puis construit une première fois le rapprochement sur la population
    ainsi chargée — ce test établit sa propre précondition plutôt que d'en hériter. Sans cette
    construction initiale, la comparaison entre le premier retrait (avant que le protocole du
    test n'ait jamais rejoué le graphe) et le second (après ses propres rejeux, qui construisent
    le rapprochement pour la première fois) porterait sur un rapprochement vide d'un côté et
    peuplé de l'autre — mesuré : la propriété échoue exactement ainsi sur un instrument où rien
    n'a jamais construit le rapprochement au préalable."""
    racine = _racine_scenario()
    for date_iso in DATES_CHRONOLOGIQUES:
        chargeur.charger_scenario(racine, date_debut=date_iso, date_fin=date_iso)
    for module in ("linkage.prediction", "linkage.evaluation"):
        resultat = subprocess.run(
            ["uv", "run", "python", "-m", module], cwd=RACINE, capture_output=True, text=True
        )
        assert resultat.returncode == 0, (
            f"construction initiale du rapprochement ({module}) échouée (code "
            f"{resultat.returncode}) :\n{resultat.stdout[-4000:]}\n{resultat.stderr[-4000:]}"
        )


def _etat_toutes_partitions(cur, n_ipps: list[str]) -> dict:
    etat: dict = {}
    for date_iso in DATES_CHRONOLOGIQUES:
        etat[date_iso] = etat_partition(cur, _date_us(date_iso), date_iso)
    etat["population"] = etat_population(cur, n_ipps)
    return etat


def _rejouer_sequence(ordre: tuple[str, ...], libelle: str) -> None:
    """Rejoue chaque date de `ordre`. Seul le DERNIER rejeu (les trois journées retirées sont
    alors toutes rechargées) doit produire un graphe intégralement vert. Pour les rejeux
    intermédiaires, seule la réussite du chargement de LA journée traitée est exigée — un échec
    de `dbt_tests` y est attendu tant que d'autres journées retirées manquent encore (voir le
    docstring du module)."""
    for i, date_iso in enumerate(ordre):
        resultat = executer_graphe(date_iso)
        dernier = i == len(ordre) - 1

        with connexion() as conn, conn.cursor() as cur:
            n_ipps = n_ipps_de_la_partition(cur, _date_us(date_iso))
        assert n_ipps, (
            f"{libelle} : le chargement de {date_iso} n'a pas restauré sa partition "
            f"(code retour du graphe {resultat.returncode})"
        )

        if dernier:
            assert resultat.returncode == 0, (
                f"{libelle} : dernier rejeu de la séquence ({date_iso}), les trois journées "
                f"retirées sont toutes rechargées, le graphe doit être intégralement vert "
                f"(code {resultat.returncode}) :\n"
                f"{resultat.stdout[-4000:]}\n{resultat.stderr[-4000:]}"
            )


def test_rattrapage_ordre_indifferent() -> None:
    verifier_base_jetable()
    preparer_orchestrateur()
    _etablir_journees()

    with connexion() as conn, conn.cursor() as cur:
        n_ipps_par_date = {}
        for date_iso in DATES_CHRONOLOGIQUES:
            n_ipps = n_ipps_de_la_partition(cur, _date_us(date_iso))
            assert n_ipps, (
                f"{date_iso} : le chargement établi par ce test lui-même n'a pas produit de "
                "fiche patient pour cette date"
            )
            n_ipps_par_date[date_iso] = n_ipps
        n_ipps_union = sorted({ipp for ipps in n_ipps_par_date.values() for ipp in ipps})

        # 1. Retrait des trois partitions : l'état doit changer.
        etat_avant_retrait = _etat_toutes_partitions(cur, n_ipps_union)
        for date_iso in DATES_CHRONOLOGIQUES:
            retirer_partition(cur, _date_us(date_iso), date_iso)
        conn.commit()
        etat_apres_retrait = _etat_toutes_partitions(cur, n_ipps_union)
        assert etat_apres_retrait != etat_avant_retrait, (
            "le retrait des trois partitions n'a rien changé à l'état mesuré : ce test ne "
            "mesurerait rien"
        )
        for date_iso in DATES_CHRONOLOGIQUES:
            for table in TABLES_SOURCE:
                assert etat_apres_retrait[date_iso][f"source.{table}"][0] == 0

    # 2. Rejeu dans l'ordre chronologique, avec mesure intermédiaire à 2 jours puis à 3 jours
    #    (contrôle de sensibilité positif).
    for date_iso in DATES_CHRONOLOGIQUES[:2]:
        resultat = executer_graphe(date_iso)
        with connexion() as conn, conn.cursor() as cur:
            n_ipps = n_ipps_de_la_partition(cur, _date_us(date_iso))
        assert n_ipps, (
            f"rejeu chronologique : le chargement de {date_iso} n'a pas restauré sa partition "
            f"(code retour du graphe {resultat.returncode})"
        )

    with connexion() as conn, conn.cursor() as cur:
        etat_a_deux_jours = _etat_toutes_partitions(cur, n_ipps_union)

    resultat = executer_graphe(DATES_CHRONOLOGIQUES[2])
    assert resultat.returncode == 0, (
        f"rejeu chronologique : dernier rejeu de la séquence ({DATES_CHRONOLOGIQUES[2]}), les "
        f"trois journées retirées sont toutes rechargées, le graphe doit être intégralement "
        f"vert (code {resultat.returncode}) :\n"
        f"{resultat.stdout[-4000:]}\n{resultat.stderr[-4000:]}"
    )

    with connexion() as conn, conn.cursor() as cur:
        etat_chronologique = _etat_toutes_partitions(cur, n_ipps_union)

    assert etat_a_deux_jours != etat_chronologique, (
        "l'état mesuré après deux jours chargés est identique à l'état après trois jours "
        "chargés : la comparaison d'état ne mesure rien (colonne oubliée ou filtre trop "
        "large) — le contrôle de sensibilité n'est pas concluant"
    )

    # 3. Retrait des trois partitions à nouveau : retour à l'état mesuré après le premier
    #    retrait initial ci-dessus, preuve que ce retrait est lui-même reproductible.
    with connexion() as conn, conn.cursor() as cur:
        for date_iso in DATES_CHRONOLOGIQUES:
            retirer_partition(cur, _date_us(date_iso), date_iso)
        conn.commit()
        etat_apres_second_retrait = _etat_toutes_partitions(cur, n_ipps_union)
    assert etat_apres_second_retrait == etat_apres_retrait, (
        "le second retrait des trois partitions ne reproduit pas l'état du premier retrait"
    )

    # 4. Rejeu dans un ordre NON chronologique : même état final que le rejeu chronologique.
    _rejouer_sequence(ORDRE_NON_CHRONOLOGIQUE, "rejeu non chronologique")

    with connexion() as conn, conn.cursor() as cur:
        etat_non_chronologique = _etat_toutes_partitions(cur, n_ipps_union)

    divergentes = [
        cle
        for cle in etat_non_chronologique
        if etat_non_chronologique[cle] != etat_chronologique.get(cle)
    ]
    assert etat_non_chronologique == etat_chronologique, (
        "l'état après rejeu dans le désordre diverge de l'état après rejeu chronologique, "
        f"clés divergentes : {divergentes}"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
