"""Contrôles bloquants sur `ingestion/chargeur.py`, sur mini-partitions fabriquées.

Connexion à la base par les mêmes variables d'environnement que `tests/test_provenance.py`
(réutilise `chargeur.connexion()`) ; si la base est injoignable, ces tests échouent plutôt
que d'être sautés. Dates de partition dédiées aux tests (2030, hors de toute période
couverte par un jeu réel ou synthétique), les deux schémas nettoyés sur ces dates avant et
après chaque test — aucun test ne dépend de l'ordre d'exécution des autres.
"""

import csv
from datetime import datetime
from pathlib import Path

import pytest

from ingestion import chargeur, controles

TABLE = "relances"
COLONNES = [e["colonne"] for e in controles.charger_registre() if e["table"] == f"source.{TABLE}"]

DATES_TEST = ["2030-01-01", "2030-01-02", "2030-01-03", "2030-01-04", "2030-01-05", "2030-01-06"]


def _mmddyyyy(date_iso: str) -> str:
    return datetime.strptime(date_iso, "%Y-%m-%d").strftime("%m/%d/%Y")


def _nettoyer(date_iso: str) -> None:
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            f"delete from source.{TABLE} where date_extraction = %s", (_mmddyyyy(date_iso),)
        )
        cur.execute(f"delete from quarantaine.{TABLE} where rejet_partition = %s", (date_iso,))


@pytest.fixture(autouse=True)
def partitions_de_test_propres():
    for date_iso in DATES_TEST:
        _nettoyer(date_iso)
    yield
    for date_iso in DATES_TEST:
        _nettoyer(date_iso)


def _ecrire_csv(chemin: Path, lignes: list[dict[str, str]]) -> None:
    with chemin.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
        ecrivain.writeheader()
        for ligne in lignes:
            ecrivain.writerow(ligne)


def _ligne(
    n_relance: str, date_iso: str, date_relance: str = "", canal: str = "EMAIL"
) -> dict[str, str]:
    return {
        "n_relance": n_relance,
        "n_creance": f"CRE-{n_relance}",
        "date_relance": date_relance or _mmddyyyy(date_iso),
        "canal": canal,
        "resultat": "SANS",
        "date_extraction": _mmddyyyy(date_iso),
    }


def _decompte_source(date_iso: str) -> int:
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            f"select count(*) from source.{TABLE} where date_extraction = %s",
            (_mmddyyyy(date_iso),),
        )
        return cur.fetchone()[0]


def _decompte_quarantaine(date_iso: str) -> int:
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            f"select count(*) from quarantaine.{TABLE} where rejet_partition = %s", (date_iso,)
        )
        return cur.fetchone()[0]


def _fichier_valide(date_iso: str, prefixe: str = "L", n: int = 20) -> list[dict[str, str]]:
    return [_ligne(f"{prefixe}{i:03d}", date_iso) for i in range(n)]


def _fichier_sous_le_seuil(date_iso: str, prefixe: str = "L") -> list[dict[str, str]]:
    """21 lignes, une seule invalide : 1/21 ≈ 4,76 %, sous le seuil de 5 %."""
    lignes = _fichier_valide(date_iso, prefixe, 20)
    lignes.append(_ligne(f"{prefixe}099", date_iso, date_relance="zzz"))
    return lignes


def _fichier_au_dessus_du_seuil(date_iso: str, prefixe: str = "S") -> list[dict[str, str]]:
    """2 lignes, une invalide : 1/2 = 50 %, au-dessus du seuil de 5 %."""
    return [
        _ligne(f"{prefixe}001", date_iso),
        _ligne(f"{prefixe}002", date_iso, date_relance="zzz"),
    ]


def test_partition_mixte_acceptees_et_rejetees(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    chemin = tmp_path / f"{TABLE}.csv"
    _ecrire_csv(chemin, _fichier_sous_le_seuil(date_iso))

    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin)

    assert resultat["etat"] == "charge"
    assert resultat["lues"] == 21
    assert resultat["inserees"] == 20
    assert resultat["rejetees"] == 1
    assert _decompte_source(date_iso) == 20
    assert _decompte_quarantaine(date_iso) == 1

    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            f"select n_relance, n_creance, date_relance, canal, resultat, rejet_motifs "
            f"from quarantaine.{TABLE} where rejet_partition = %s",
            (date_iso,),
        )
        ligne = cur.fetchone()
    assert ligne == ("L099", "CRE-L099", "zzz", "EMAIL", "SANS", "typage_date:date_relance:zzz")


def test_idempotence_meme_fichier_deux_fois(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    chemin = tmp_path / f"{TABLE}.csv"
    _ecrire_csv(chemin, _fichier_sous_le_seuil(date_iso))

    chargeur.charger_table_partition(TABLE, date_iso, chemin)
    decompte_source_1 = _decompte_source(date_iso)
    decompte_quarantaine_1 = _decompte_quarantaine(date_iso)

    chargeur.charger_table_partition(TABLE, date_iso, chemin)
    decompte_source_2 = _decompte_source(date_iso)
    decompte_quarantaine_2 = _decompte_quarantaine(date_iso)

    assert decompte_source_2 == decompte_source_1
    assert decompte_quarantaine_2 == decompte_quarantaine_1


def test_remplacement_exact_apres_modification(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    chemin = tmp_path / f"{TABLE}.csv"
    lignes = _fichier_sous_le_seuil(date_iso)
    _ecrire_csv(chemin, lignes)
    chargeur.charger_table_partition(TABLE, date_iso, chemin)
    decompte_avant = _decompte_source(date_iso)

    lignes[0] = dict(lignes[0], canal="COUR")
    _ecrire_csv(chemin, lignes)
    chargeur.charger_table_partition(TABLE, date_iso, chemin)
    decompte_apres = _decompte_source(date_iso)

    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            f"select canal from source.{TABLE} where n_relance = %s", (lignes[0]["n_relance"],)
        )
        (canal,) = cur.fetchone()
        cur.execute(
            f"select count(*) from source.{TABLE} where n_relance = %s and canal = %s",
            (lignes[0]["n_relance"], "EMAIL"),
        )
        (compte_ancienne_valeur,) = cur.fetchone()

    assert canal == "COUR"
    assert compte_ancienne_valeur == 0
    assert decompte_apres == decompte_avant


def test_seuil_bloque_et_contenu_anterieur_survit(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    chemin_ok = tmp_path / "ok.csv"
    _ecrire_csv(chemin_ok, _fichier_sous_le_seuil(date_iso))
    chargeur.charger_table_partition(TABLE, date_iso, chemin_ok)
    decompte_source_avant = _decompte_source(date_iso)
    decompte_quarantaine_avant = _decompte_quarantaine(date_iso)
    assert decompte_source_avant > 0

    chemin_bloque = tmp_path / "bloque.csv"
    _ecrire_csv(chemin_bloque, _fichier_au_dessus_du_seuil(date_iso))
    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin_bloque)

    assert resultat["etat"] == "bloque_seuil"
    assert resultat["lues"] == 2
    assert resultat["rejetees"] == 1
    assert _decompte_source(date_iso) == decompte_source_avant
    assert _decompte_quarantaine(date_iso) == decompte_quarantaine_avant


def test_atomicite_sur_echec_en_cours_d_insertion(tmp_path: Path, monkeypatch) -> None:
    date_iso = "2030-01-01"
    chemin_ok = tmp_path / "ok.csv"
    _ecrire_csv(chemin_ok, _fichier_sous_le_seuil(date_iso))
    chargeur.charger_table_partition(TABLE, date_iso, chemin_ok)
    decompte_source_avant = _decompte_source(date_iso)
    decompte_quarantaine_avant = _decompte_quarantaine(date_iso)
    assert decompte_source_avant > 0
    assert decompte_quarantaine_avant > 0

    def echoue(*args, **kwargs):
        raise RuntimeError("panne simulée en cours d'insertion")

    monkeypatch.setattr(chargeur, "_inserer_quarantaine", echoue)

    chemin_nouveau = tmp_path / "nouveau.csv"
    _ecrire_csv(chemin_nouveau, _fichier_sous_le_seuil(date_iso, prefixe="N"))

    with pytest.raises(RuntimeError, match="panne simulée"):
        chargeur.charger_table_partition(TABLE, date_iso, chemin_nouveau)

    assert _decompte_source(date_iso) == decompte_source_avant
    assert _decompte_quarantaine(date_iso) == decompte_quarantaine_avant


def test_partition_incoherente(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    autre_jour = "2030-01-02"
    chemin = tmp_path / f"{TABLE}.csv"
    lignes = _fichier_valide(date_iso)
    ligne_incoherente = dict(lignes[0])
    ligne_incoherente["date_extraction"] = _mmddyyyy(autre_jour)
    lignes[0] = ligne_incoherente
    _ecrire_csv(chemin, lignes)

    chargeur.charger_table_partition(TABLE, date_iso, chemin)

    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(
            f"select rejet_motifs from quarantaine.{TABLE} "
            f"where rejet_partition = %s and n_relance = %s",
            (date_iso, ligne_incoherente["n_relance"]),
        )
        (motifs,) = cur.fetchone()

    assert f"partition_incoherente:date_extraction:{_mmddyyyy(autre_jour)}" in motifs.split(";")


def test_entete_invalide_permute_refuse_sans_ecriture(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    chemin = tmp_path / f"{TABLE}.csv"
    colonnes_permutees = [COLONNES[1], COLONNES[0], *COLONNES[2:]]
    with chemin.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=colonnes_permutees)
        ecrivain.writeheader()
        ecrivain.writerow(_ligne("PERM001", date_iso))

    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin)

    assert resultat["etat"] == "en_tete_invalide"
    assert resultat["lues"] == 0
    assert resultat["inserees"] == 0
    assert _decompte_source(date_iso) == 0
    assert _decompte_quarantaine(date_iso) == 0


def test_entete_invalide_tronque_refuse_sans_ecriture(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    chemin = tmp_path / f"{TABLE}.csv"
    colonnes_tronquees = COLONNES[:-1]
    with chemin.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.DictWriter(f, fieldnames=colonnes_tronquees)
        ecrivain.writeheader()

    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin)

    assert resultat["etat"] == "en_tete_invalide"
    assert _decompte_source(date_iso) == 0
    assert _decompte_quarantaine(date_iso) == 0


def test_charger_partition_ignore_tables_absentes(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    _ecrire_csv(tmp_path / f"{TABLE}.csv", [])

    resultats = chargeur.charger_partition(date_iso, tmp_path)

    assert TABLE in resultats
    assert resultats[TABLE]["etat"] == "charge"
    assert len(resultats) == 1
