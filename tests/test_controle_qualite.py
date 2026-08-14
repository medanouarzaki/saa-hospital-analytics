"""Contrôle de qualité journalier (`ingestion/controle_qualite.py`) : passe sur une journée
normale, échoue sur une journée dégradée. Les deux journées sont construites sur l'instrument
jetable, sur une seule table (`creances`) et deux dates inutilisées ailleurs sur cet instrument,
pour ne dépendre d'aucun autre chargement déjà en place. La propriété comparée est le taux de
rejet cumulé, calculé indépendamment par ce test à partir de `decompte_journee`, face au seuil
chargé par `ingestion.controles.charger_config()` — jamais un littéral.
"""

import csv
import os
from datetime import datetime
from pathlib import Path

import pytest

from ingestion import chargeur, controles
from ingestion.controle_qualite import decompte_journee, evaluer

RACINE = Path(__file__).resolve().parent.parent
RACINE_SCENARIO = Path(
    os.environ.get("SAA_SCENARIO_ROOT", str(RACINE / "generator" / "output" / "scenario_30"))
)

DATE_NORMALE = "2024-04-15"
DATE_DEGRADEE = "2024-04-16"
N_CORROMPUES = 1
N_LIGNES_MINIMUM = 2


def _meilleure_partition_reference() -> tuple[Path, int]:
    """La partition `creances` la mieux fournie du scénario actif — le nombre de lignes
    disponibles par date varie avec le sous-ensemble (copié, généré, complet), donc jamais une
    date ni un décompte fixés d'avance."""
    dossier = RACINE_SCENARIO / "source.creances"
    candidats = []
    for chemin in dossier.glob("*/creances.csv"):
        with chemin.open(encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1
        candidats.append((n, chemin))
    n, chemin = max(candidats)
    assert n >= N_LIGNES_MINIMUM, (
        f"aucune partition creances de {RACINE_SCENARIO} ne porte au moins {N_LIGNES_MINIMUM} "
        f"lignes (meilleure trouvée : {chemin} avec {n})"
    )
    return chemin, n


FICHIER_REFERENCE, N_LIGNES = _meilleure_partition_reference()


def verifier_base_jetable() -> None:
    if os.environ.get("SAA_INSTRUMENT_JETABLE") != "1":
        pytest.fail(
            "SAA_INSTRUMENT_JETABLE doit valoir '1' pour exécuter ce test : il charge des "
            "lignes construites, dont des lignes délibérément invalides, sur la cible visée."
        )


def _construire_fichier(chemin_dest: Path, date_us: str, n_corrompues: int) -> None:
    with FICHIER_REFERENCE.open(newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        entete = next(lecteur)
        lignes = [next(lecteur) for _ in range(N_LIGNES)]

    idx_date_extraction = entete.index("date_extraction")
    idx_date_naissance = entete.index("date_naissance_creance")
    idx_n_creance = entete.index("n_creance")

    for i, ligne in enumerate(lignes):
        ligne[idx_date_extraction] = date_us
        ligne[idx_n_creance] = f"{ligne[idx_n_creance]}-{date_us.replace('/', '')}"
        if i < n_corrompues:
            ligne[idx_date_naissance] = "PAS-UNE-DATE"

    chemin_dest.parent.mkdir(parents=True, exist_ok=True)
    with chemin_dest.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(entete)
        ecrivain.writerows(lignes)


def _preparer_journee(tmp_path: Path, date_iso: str, n_corrompues: int) -> None:
    date_us_valeur = datetime.strptime(date_iso, "%Y-%m-%d").strftime(chargeur._FORMAT_DATE)
    chemin = tmp_path / "creances.csv"
    _construire_fichier(chemin, date_us_valeur, n_corrompues)
    resultat = chargeur.charger_table_partition("creances", date_iso, chemin)
    assert resultat["etat"] == "charge", (
        f"préparation de {date_iso} : fichier non chargé (état {resultat['etat']!r}) — la "
        "dégradation de ce test dépasserait la garde du chargeur, ce n'est pas ce qu'il teste"
    )


def test_controle_qualite_journee_normale_puis_degradee(tmp_path: Path) -> None:
    verifier_base_jetable()
    seuil = controles.charger_config()["seuil_quarantaine"]["valeur"]

    # Journée normale : aucune ligne corrompue.
    _preparer_journee(tmp_path, DATE_NORMALE, n_corrompues=0)
    decomptes_normale = decompte_journee(DATE_NORMALE)
    total_charges = sum(d["charges"] for d in decomptes_normale.values())
    total_rejetes = sum(d["rejetes"] for d in decomptes_normale.values())
    taux_normale = total_rejetes / (total_charges + total_rejetes)
    assert taux_normale <= seuil, (
        f"journée normale de contrôle : taux {taux_normale} déjà au-dessus du seuil {seuil}, "
        "ce test ne construit pas ce qu'il croit construire"
    )

    reussite_normale, message_normale = evaluer(DATE_NORMALE)
    assert reussite_normale is True, (
        f"le contrôle échoue sur une journée dont le taux mesuré ({taux_normale}) est sous le "
        f"seuil ({seuil}) : {message_normale}"
    )

    # Journée dégradée : une ligne sur dix rendue invalide par un motif déjà connu de la
    # quarantaine (date de naissance de créance mal formée, ingestion/controles.py) — sous le
    # plancher de la garde du chargeur (elle n'exige que 2 rejets), donc chargée normalement.
    _preparer_journee(tmp_path, DATE_DEGRADEE, n_corrompues=N_CORROMPUES)
    decomptes_degradee = decompte_journee(DATE_DEGRADEE)
    total_charges_d = sum(d["charges"] for d in decomptes_degradee.values())
    total_rejetes_d = sum(d["rejetes"] for d in decomptes_degradee.values())
    taux_degradee = total_rejetes_d / (total_charges_d + total_rejetes_d)
    assert taux_degradee > seuil, (
        f"journée dégradée de contrôle : taux {taux_degradee} encore sous le seuil {seuil}, "
        "la dégradation construite par ce test ne le dépasse pas"
    )

    reussite_degradee, message_degradee = evaluer(DATE_DEGRADEE)
    assert reussite_degradee is False, (
        f"le contrôle réussit sur une journée dont le taux mesuré ({taux_degradee}) dépasse le "
        f"seuil ({seuil}) : {message_degradee}"
    )
    assert str(seuil) in message_degradee or f"{seuil:.4f}" in message_degradee, (
        f"le message d'échec ne nomme pas le seuil : {message_degradee}"
    )
    assert "creances" in message_degradee, (
        f"le message d'échec ne porte pas la ventilation par table : {message_degradee}"
    )
