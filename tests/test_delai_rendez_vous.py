"""Conformité du délai de rendez-vous, de la configuration du générateur jusqu'à
marts.agg_delai_rendez_vous. C'est le contrôle qui porte le critère central du bloc :
la chaîne complète (génération -> chargement -> dbt) ne déforme pas le signal du
paramètre de délai médian par activité.

Exige une base avec dbt exécuté (marts.agg_delai_rendez_vous) ; ne s'exécute utilement
que dans le job CI dédié ou contre une base Compose locale déjà chargée et
dbt-runnée. Connexion base paramétrable par variable d'environnement, même mécanisme
que tests/test_dim_patient.py. Aucun skip silencieux : base manquante fait échouer le
test.
"""

import importlib.util
import math
from pathlib import Path

import psycopg
import pytest

from generator import config

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

# Plancher : résolution de la comparaison -- le délai observé est un entier de jours,
# le paramètre de configuration un réel, la comparaison ne peut donc jamais viser
# mieux qu'un jour d'écart.
PLANCHER_JOURS = 1

# Marge statistique : la médiane d'un échantillon fini d'une loi log-normale fluctue
# autour de la médiane de la loi, d'autant plus que l'échantillon est petit. La
# tolérance doit rester vraie que la population comparée vienne d'une génération
# complète ou d'un sous-ensemble réduit, sans qu'aucun littéral de volumétrie
# n'y apparaisse : c'est ce terme, proportionnel à l'erreur type asymptotique de la
# médiane, qui porte cette dépendance à la taille d'échantillon.
FACTEUR_TOLERANCE = 3


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
            f"connexion impossible à la base ({exc}) : marts.agg_delai_rendez_vous doit "
            "être chargée et dbt exécuté avant ce test"
        )


def _lignes_agregat() -> list[dict]:
    conn = _connexion()
    try:
        with conn.cursor() as curseur:
            curseur.execute(
                "select code_activite, n_delai_positif, mediane_delai_positif_jours, "
                "ecart_type_log_delai_positif from marts.agg_delai_rendez_vous"
            )
            colonnes = [c.name for c in curseur.description]
            return [dict(zip(colonnes, ligne, strict=True)) for ligne in curseur.fetchall()]
    finally:
        conn.close()


def test_ensembles_codes_activite_coincident() -> None:
    lignes = _lignes_agregat()
    codes_agregat = {ligne["code_activite"] for ligne in lignes}
    codes_config = set(config.valeur("delai_rdv_par_specialite").keys())
    assert codes_agregat == codes_config, (codes_agregat, codes_config)


def test_mediane_delai_positif_dans_tolerance() -> None:
    # Population de comparaison : délai strictement positif. Le générateur
    # court-circuite le tirage de la loi log-normale pour les rendez-vous pris le jour
    # même (délai nul) -- une décision de construction, pas un tirage de la loi ; les
    # mélanger à la population de comparaison biaiserait la médiane observée vers le
    # bas, sans rapport avec le paramètre lui-même.
    lignes = _lignes_agregat()
    mediane_config = config.valeur("delai_rdv_par_specialite")

    echecs = []
    for ligne in lignes:
        code = ligne["code_activite"]
        effectif = ligne["n_delai_positif"]
        mediane_mesuree = float(ligne["mediane_delai_positif_jours"])
        sigma_log = float(ligne["ecart_type_log_delai_positif"])
        mediane_attendue = mediane_config[code]

        ecart = abs(mediane_mesuree - mediane_attendue)
        erreur_type = mediane_mesuree * sigma_log * math.sqrt(math.pi / 2) / math.sqrt(effectif)
        tolerance = max(PLANCHER_JOURS, FACTEUR_TOLERANCE * erreur_type)

        if ecart > tolerance:
            echecs.append(
                f"activité {code} : médiane mesurée {mediane_mesuree}, médiane attendue "
                f"{mediane_attendue}, écart {ecart:.4f}, tolérance {tolerance:.4f}"
            )

    assert not echecs, "\n".join(echecs)
