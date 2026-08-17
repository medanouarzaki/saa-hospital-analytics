"""Contrôle de qualité journalier (`ingestion/controle_qualite.py`) : passe sur une journée
normale, échoue sur une journée dégradée. Les deux journées sont construites sur l'instrument
jetable, sur une seule table (`creances`) et deux dates inutilisées ailleurs sur cet instrument,
pour ne dépendre d'aucun autre chargement déjà en place. La propriété comparée est le taux de
rejet cumulé, calculé indépendamment par ce test à partir de `decompte_journee`, face au seuil
chargé par `ingestion.controles.charger_config()` — jamais un littéral.

**Les deux dates sont DÉRIVÉES, jamais écrites.** Une date écrite d'avance n'est vide que sur le
jeu pour lequel elle a été choisie : mesuré, deux dates d'avril 2024 portaient 214 lignes
légitimes sur le scénario complet, si bien que l'unique ligne corrompue donnait un taux de
0,466 % — sous le seuil, et le contrôle rougissait sans qu'aucune régression n'ait eu lieu. Les
dates se prennent donc **après la dernière date du scénario actif**, ce qui les rend vides quel
que soit le sous-ensemble chargé, et le choix ne dépend que des fichiers du scénario : deux
exécutions sur le même jeu retiennent les deux mêmes dates. Comme ce test y écrit lui-même, il
efface ses propres lignes à ces dates avant de s'en servir — un test établit ses préconditions
plutôt que d'en hériter, y compris d'un de ses passages antérieurs.

**Le nombre de lignes de la partition de référence est dérivé lui aussi.** La journée dégradée
doit dépasser le seuil avec une seule ligne corrompue — sans quoi le chargeur bloquerait le
fichier au lieu de le charger, ce que ce test ne vérifie pas — donc `1 / lignes > seuil`, donc
moins de `1 / seuil` lignes. La borne vient du seuil chargé, non d'un décompte écrit.
"""

import csv
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from ingestion import chargeur, controles
from ingestion.controle_qualite import decompte_journee, evaluer

RACINE = Path(__file__).resolve().parent.parent

N_CORROMPUES = 1


def _racine_scenario() -> Path:
    """Évaluée à l'appel, jamais à l'import : `SAA_SCENARIO_ROOT` n'est pas garantie exportée
    au seul chargement de ce module (par exemple à la collecte pytest)."""
    return Path(
        os.environ.get("SAA_SCENARIO_ROOT", str(RACINE / "generator" / "output" / "scenario_30"))
    )


def _partition_reference(seuil: float) -> tuple[Path, int]:
    """La partition `creances` la mieux fournie parmi celles qui rendent la propriété
    vérifiable — le nombre de lignes disponibles par date varie avec le sous-ensemble (copié,
    généré, complet), donc jamais une date ni un décompte fixés d'avance. Évaluée à l'appel,
    jamais à l'import : un scénario n'est pas garanti présent au seul chargement de ce module
    (par exemple à la collecte pytest).

    Les deux bornes sont dérivées et non écrites. En haut : une seule ligne corrompue doit
    porter le taux au-dessus du seuil, donc `1 / lignes > seuil`, donc `lignes < 1 / seuil`. En
    bas : le plancher de rejets bloquants du chargeur, pour que la journée porte plus que sa
    seule ligne corrompue.
    """
    racine_scenario = _racine_scenario()
    plancher = controles.charger_config()["plancher_rejets_bloquants"]["valeur"]
    lignes_maximum_exclu = 1 / seuil
    dossier = racine_scenario / "source.creances"
    candidats = []
    eligibles = []
    for chemin in dossier.glob("*/creances.csv"):
        with chemin.open(encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1
        candidats.append((n, chemin))
        if plancher <= n < lignes_maximum_exclu:
            eligibles.append((n, chemin))
    assert candidats, f"aucune partition creances trouvée sous {dossier}"
    assert eligibles, (
        f"aucune partition creances de {racine_scenario} ne porte entre {plancher} et "
        f"{lignes_maximum_exclu} lignes : avec une seule ligne corrompue, aucune journée "
        f"construite depuis ce scénario ne peut dépasser le seuil {seuil} sans que le chargeur "
        f"ne bloque le fichier (meilleure partition trouvée : {max(candidats)[1]} avec "
        f"{max(candidats)[0]} lignes)"
    )
    n, chemin = max(eligibles)
    return chemin, n


def _dates_derivees() -> tuple[str, str]:
    """Deux dates consécutives que le scénario actif ne couvre pas, donc absentes de toute base
    chargée depuis lui — condition sans laquelle le dénominateur du taux échappe à ce test.

    Le choix ne dépend que des répertoires de partition du scénario, jamais du contenu de la
    base : deux exécutions sur le même jeu retiennent les deux mêmes dates, y compris après que
    la première y a écrit ses propres lignes.
    """
    dossier = _racine_scenario() / "source.creances"
    dates = sorted(p.name for p in dossier.iterdir() if p.is_dir())
    assert dates, (
        f"aucune partition datée sous {dossier} : impossible de dériver une date que le "
        "scénario ne couvre pas"
    )
    derniere = date.fromisoformat(dates[-1])
    return (
        (derniere + timedelta(days=1)).isoformat(),
        (derniere + timedelta(days=2)).isoformat(),
    )


def _effacer_journee(date_iso: str) -> None:
    """Efface les lignes que ce test a pu laisser à cette date lors d'un passage antérieur. La
    date étant hors du scénario, aucune autre écriture ne peut y avoir déposé quoi que ce soit.
    """
    date_us = datetime.strptime(date_iso, "%Y-%m-%d").strftime(chargeur._FORMAT_DATE)
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "select table_name from information_schema.tables where table_schema = 'source'"
        )
        for (table,) in cur.fetchall():
            cur.execute(f'delete from source."{table}" where date_extraction = %s', (date_us,))
            cur.execute(
                f'delete from quarantaine."{table}" where rejet_partition = %s', (date_iso,)
            )
        conn.commit()


def verifier_base_jetable() -> None:
    if os.environ.get("SAA_INSTRUMENT_JETABLE") != "1":
        pytest.fail(
            "SAA_INSTRUMENT_JETABLE doit valoir '1' pour exécuter ce test : il charge des "
            "lignes construites, dont des lignes délibérément invalides, sur la cible visée."
        )


def _construire_fichier(chemin_dest: Path, date_us: str, n_corrompues: int, seuil: float) -> None:
    fichier_reference, n_lignes = _partition_reference(seuil)
    with fichier_reference.open(newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        entete = next(lecteur)
        lignes = [next(lecteur) for _ in range(n_lignes)]

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


def _preparer_journee(tmp_path: Path, date_iso: str, n_corrompues: int, seuil: float) -> None:
    _effacer_journee(date_iso)
    date_us_valeur = datetime.strptime(date_iso, "%Y-%m-%d").strftime(chargeur._FORMAT_DATE)
    chemin = tmp_path / f"creances_{date_iso}.csv"
    _construire_fichier(chemin, date_us_valeur, n_corrompues, seuil)
    resultat = chargeur.charger_table_partition("creances", date_iso, chemin)
    assert resultat["etat"] == "charge", (
        f"préparation de {date_iso} : fichier non chargé (état {resultat['etat']!r}) — la "
        "dégradation de ce test dépasserait la garde du chargeur, ce n'est pas ce qu'il teste"
    )


def test_controle_qualite_journee_normale_puis_degradee(tmp_path: Path) -> None:
    verifier_base_jetable()
    seuil = controles.charger_config()["seuil_quarantaine"]["valeur"]
    date_normale, date_degradee = _dates_derivees()

    # Journée normale : aucune ligne corrompue.
    _preparer_journee(tmp_path, date_normale, n_corrompues=0, seuil=seuil)
    decomptes_normale = decompte_journee(date_normale)
    total_charges = sum(d["charges"] for d in decomptes_normale.values())
    total_rejetes = sum(d["rejetes"] for d in decomptes_normale.values())
    taux_normale = total_rejetes / (total_charges + total_rejetes)
    assert taux_normale <= seuil, (
        f"journée normale de contrôle ({date_normale}) : taux {taux_normale} déjà au-dessus du "
        f"seuil {seuil}, ce test ne construit pas ce qu'il croit construire"
    )

    reussite_normale, message_normale = evaluer(date_normale)
    assert reussite_normale is True, (
        f"le contrôle échoue sur une journée ({date_normale}) dont le taux mesuré "
        f"({taux_normale}) est sous le seuil ({seuil}) : {message_normale}"
    )

    # Journée dégradée : une ligne sur dix rendue invalide par un motif déjà connu de la
    # quarantaine (date de naissance de créance mal formée, ingestion/controles.py) — sous le
    # plancher de la garde du chargeur (elle n'exige que 2 rejets), donc chargée normalement.
    _preparer_journee(tmp_path, date_degradee, n_corrompues=N_CORROMPUES, seuil=seuil)
    decomptes_degradee = decompte_journee(date_degradee)
    total_charges_d = sum(d["charges"] for d in decomptes_degradee.values())
    total_rejetes_d = sum(d["rejetes"] for d in decomptes_degradee.values())
    taux_degradee = total_rejetes_d / (total_charges_d + total_rejetes_d)
    assert taux_degradee > seuil, (
        f"journée dégradée de contrôle ({date_degradee}) : taux {taux_degradee} encore sous le "
        f"seuil {seuil}, la dégradation construite par ce test ne le dépasse pas — cette date "
        f"porte {total_charges_d + total_rejetes_d} lignes, dont {total_rejetes_d} rejetée(s)"
    )

    reussite_degradee, message_degradee = evaluer(date_degradee)
    assert reussite_degradee is False, (
        f"le contrôle réussit sur une journée ({date_degradee}) dont le taux mesuré "
        f"({taux_degradee}) dépasse le seuil ({seuil}) : {message_degradee}"
    )
    assert str(seuil) in message_degradee or f"{seuil:.4f}" in message_degradee, (
        f"le message d'échec ne nomme pas le seuil : {message_degradee}"
    )
    assert "creances" in message_degradee, (
        f"le message d'échec ne porte pas la ventilation par table : {message_degradee}"
    )
