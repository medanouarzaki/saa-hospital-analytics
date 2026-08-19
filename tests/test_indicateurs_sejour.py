"""Recalcule les quatre indicateurs hospitaliers (TOM, DMS, TROT, IROT) depuis
marts.fct_sejour et les confronte aux valeurs publiées lues dans la configuration.

Formules et traitement des séjours non clos (prolongés jusqu'à la borne de fin de
période) repris de tests/test_coherence_inter_tables.py::
test_regle_13_indicateurs_sejour_recalcules_depuis_les_donnees (lignes 333-375) : la
valeur recalculée depuis l'entrepôt doit être comparable à celle déjà vérifiée en
amont sur les données du générateur, sinon la comparaison ne prouve rien. La
constante de tolérance de ce même fichier (TOLERANCE_RELATIVE = 0.03, ligne 371) est
une variable locale à sa fonction, non importable ; recopiée ici.

Ces quatre grandeurs sont annualisées et définies sur la période complète de
génération. Sur une fenêtre partielle, la prolongation des séjours non clos jusqu'à
la borne de période domine le calcul et l'écart sort de la tolérance -- mesuré à
l'écriture de ce test. Le test s'abstient donc, avec un motif explicite, lorsque la
date d'admission maximale présente dans marts.fct_sejour ne coïncide pas avec la
date de fin de période lue dans la configuration -- une égalité mesurée en base et en
configuration, jamais une marge arbitraire.

Exige une base avec dbt exécuté (marts.fct_sejour) ; connexion base paramétrable par
variable d'environnement, même mécanisme que tests/test_dim_patient.py. Aucun skip
silencieux hors de la garde d'applicabilité documentée ci-dessus : base manquante
fait échouer le test.
"""

import importlib.util
from datetime import UTC, date, datetime, time
from pathlib import Path

import psycopg
import pytest

from generator import config

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

TOLERANCE_RELATIVE = 0.03


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
            f"connexion impossible à la base ({exc}) : marts.fct_sejour doit être "
            "chargée et dbt exécuté avant ce test"
        )


def _sejours(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor() as curseur:
        curseur.execute("select date_heure_admission, date_heure_sortie from marts.fct_sejour")
        colonnes = [c.name for c in curseur.description]
        return [dict(zip(colonnes, ligne, strict=True)) for ligne in curseur.fetchall()]


def _max_jour_admission(conn: psycopg.Connection) -> date | None:
    with conn.cursor() as curseur:
        curseur.execute("select max(jour_admission) from marts.fct_sejour")
        (valeur,) = curseur.fetchone()
        return valeur


def test_indicateurs_sejour_recalcules_depuis_fct_sejour() -> None:
    conn = _connexion()
    try:
        max_admission = _max_jour_admission(conn)
        date_fin = date.fromisoformat(config.valeur("date_fin"))
        if max_admission != date_fin:
            pytest.skip(
                f"fenêtre chargée partielle : date d'admission maximale de "
                f"marts.fct_sejour ({max_admission}) != date de fin de période "
                f"configurée ({date_fin}) -- les quatre indicateurs, annualisés sur "
                "la période complète, ne sont comparables aux valeurs publiées que "
                "sur une génération couvrant cette période dans son entier"
            )

        date_debut = date.fromisoformat(config.valeur("date_debut"))
        n_jours_periode = (date_fin - date_debut).days + 1
        capacite = config.valeur("capacite_litiere_fonctionnelle")
        jours_an = config.valeur("jours_annee_reference")

        lignes = _sejours(conn)
    finally:
        conn.close()

    # Serveur en UTC (`show timezone`, vérifié avant d'écrire) : les colonnes
    # timestamptz de fct_sejour reviennent avec un fuseau, la borne construite ici
    # doit en porter un aussi pour rester comparable.
    borne_fin = datetime.combine(date_fin, time(23, 59, 59), tzinfo=UTC)
    total_journees = 0.0
    for ligne in lignes:
        fin = ligne["date_heure_sortie"] if ligne["date_heure_sortie"] is not None else borne_fin
        total_journees += (fin - ligne["date_heure_admission"]).total_seconds() / 86400

    journees_annuelles = total_journees * 365 / n_jours_periode
    admissions_annuelles_mesure = len(lignes) * 365 / n_jours_periode

    tom_mesure = journees_annuelles / (capacite * jours_an) * 100
    dms_mesure = journees_annuelles / admissions_annuelles_mesure
    trot_mesure = admissions_annuelles_mesure / capacite
    irot_mesure = (capacite * jours_an - journees_annuelles) / admissions_annuelles_mesure

    publies = {
        "TOM": (tom_mesure, config.valeur("tom_publie")),
        "DMS": (dms_mesure, config.valeur("dms_publie")),
        "TROT": (trot_mesure, config.valeur("trot_publie")),
        "IROT": (irot_mesure, config.valeur("irot_publie")),
    }

    echecs = []
    for nom, (mesure, cible) in publies.items():
        ecart_relatif = abs(mesure - cible) / cible
        if ecart_relatif > TOLERANCE_RELATIVE:
            echecs.append(
                f"{nom} : mesuré {mesure:.4f}, publié {cible}, écart relatif "
                f"{ecart_relatif:.4%}, tolérance {TOLERANCE_RELATIVE:.0%}"
            )

    assert not echecs, "\n".join(echecs)
