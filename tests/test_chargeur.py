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

_CONFIG = controles.charger_config()
SEUIL_QUARANTAINE = _CONFIG["seuil_quarantaine"]["valeur"]
PLANCHER_REJETS_BLOQUANTS = _CONFIG["plancher_rejets_bloquants"]["valeur"]

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


# Décomptes de rejets fixés en dur, délibérément non recalculés depuis
# PLANCHER_REJETS_BLOQUANTS : le nombre de lignes fabriquées doit rester un fait figé,
# établi une fois pour toutes contre le plancher tel qu'il est déclaré aujourd'hui (2).
# S'il était recalculé depuis la configuration à chaque exécution, muter le plancher dans
# la configuration ferait dériver le fichier fabriqué en même temps que le code testé, et
# la mutation ne serait jamais observable (les deux prémisses -- fichier et plancher --
# évolueraient toujours ensemble). SEUIL_QUARANTAINE, lui, reste lu dynamiquement pour
# n'inscrire aucun littéral de pourcentage dans ce fichier.
N_REJETS_SOUS_PLANCHER_ACTUEL = 1  # PLANCHER_REJETS_BLOQUANTS (2) moins un
N_REJETS_AU_PLANCHER_ACTUEL = 2  # PLANCHER_REJETS_BLOQUANTS (2)


def _fichier_rejets_sous_plancher(date_iso: str, prefixe: str = "U") -> list[dict[str, str]]:
    """Taux au-dessus du seuil, mais rejets sous le plancher actuel : ne doit pas être bloqué."""
    lignes = _fichier_valide(date_iso, prefixe, 1)
    for i in range(N_REJETS_SOUS_PLANCHER_ACTUEL):
        lignes.append(_ligne(f"{prefixe}9{i:02d}", date_iso, date_relance="zzz"))
    return lignes


def _fichier_rejets_au_plancher(date_iso: str, prefixe: str = "B") -> list[dict[str, str]]:
    """Taux au-dessus du seuil, rejets égaux au plancher actuel : doit être bloqué."""
    lignes = _fichier_valide(date_iso, prefixe, 1)
    for i in range(N_REJETS_AU_PLANCHER_ACTUEL):
        lignes.append(_ligne(f"{prefixe}9{i:02d}", date_iso, date_relance="zzz"))
    return lignes


def _fichier_grande_partition_sous_le_seuil(
    date_iso: str, prefixe: str = "G"
) -> list[dict[str, str]]:
    """Grande partition : rejets au plancher actuel, mais taux sous le seuil — ne doit pas
    être bloqué. Sépare la conjonction (seuil ET plancher) de la disjonction (seuil OU
    plancher), qu'aucun des autres fichiers fabriqués de ce module ne distingue : eux
    dépassent toujours le seuil en pourcentage, cette fixture-ci reste en dessous.
    """
    n_valides = int(N_REJETS_AU_PLANCHER_ACTUEL / SEUIL_QUARANTAINE) + 10
    lignes = _fichier_valide(date_iso, prefixe, n_valides)
    for i in range(N_REJETS_AU_PLANCHER_ACTUEL):
        lignes.append(_ligne(f"{prefixe}9{i:02d}", date_iso, date_relance="zzz"))
    return lignes


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
    _ecrire_csv(chemin_bloque, _fichier_rejets_au_plancher(date_iso))
    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin_bloque)

    assert resultat["etat"] == "bloque_seuil"
    assert resultat["lues"] == 1 + N_REJETS_AU_PLANCHER_ACTUEL
    assert resultat["rejetees"] == N_REJETS_AU_PLANCHER_ACTUEL
    assert _decompte_source(date_iso) == decompte_source_avant
    assert _decompte_quarantaine(date_iso) == decompte_quarantaine_avant


def test_rejet_isole_sous_plancher_charge_normalement(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    lignes = _fichier_rejets_sous_plancher(date_iso)
    n_rejets_attendus = N_REJETS_SOUS_PLANCHER_ACTUEL
    chemin = tmp_path / f"{TABLE}.csv"
    _ecrire_csv(chemin, lignes)

    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin)

    assert resultat["etat"] == "charge"
    assert resultat["lues"] == len(lignes)
    assert resultat["rejetees"] == n_rejets_attendus
    assert resultat["inserees"] == len(lignes) - n_rejets_attendus
    assert _decompte_source(date_iso) == len(lignes) - n_rejets_attendus
    assert _decompte_quarantaine(date_iso) == n_rejets_attendus


def test_rejets_au_plancher_bloque_aucune_ecriture(tmp_path: Path) -> None:
    date_iso = "2030-01-01"
    lignes = _fichier_rejets_au_plancher(date_iso)
    chemin = tmp_path / f"{TABLE}.csv"
    _ecrire_csv(chemin, lignes)

    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin)

    assert resultat["etat"] == "bloque_seuil"
    assert resultat["lues"] == len(lignes)
    assert resultat["rejetees"] == N_REJETS_AU_PLANCHER_ACTUEL
    assert resultat["inserees"] == 0
    assert _decompte_source(date_iso) == 0
    assert _decompte_quarantaine(date_iso) == 0


def test_grande_partition_sous_le_seuil_charge_malgre_le_plancher_atteint(
    tmp_path: Path,
) -> None:
    date_iso = "2030-01-01"
    lignes = _fichier_grande_partition_sous_le_seuil(date_iso)
    assert N_REJETS_AU_PLANCHER_ACTUEL / len(lignes) <= SEUIL_QUARANTAINE
    chemin = tmp_path / f"{TABLE}.csv"
    _ecrire_csv(chemin, lignes)

    resultat = chargeur.charger_table_partition(TABLE, date_iso, chemin)

    assert resultat["etat"] == "charge"
    assert resultat["rejetees"] == N_REJETS_AU_PLANCHER_ACTUEL
    assert _decompte_source(date_iso) == len(lignes) - N_REJETS_AU_PLANCHER_ACTUEL
    assert _decompte_quarantaine(date_iso) == N_REJETS_AU_PLANCHER_ACTUEL


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


DATES_SCENARIO = ["2030-03-01", "2030-03-02"]
TABLE_2 = "creances"
COLONNES_2 = [
    e["colonne"] for e in controles.charger_registre() if e["table"] == f"source.{TABLE_2}"
]


def _ligne_creances(n_creance: str, date_iso: str) -> dict[str, str]:
    return {
        "n_creance": n_creance,
        "n_facture": f"FAC-{n_creance}",
        "date_naissance_creance": _mmddyyyy(date_iso),
        "montant_du": "100.00",
        "montant_recouvre": "0.00",
        "montant_restant": "100.00",
        "type_debiteur": "PART",
        "motif_non_recouvrement": "",
        "date_extraction": _mmddyyyy(date_iso),
    }


def _nettoyer_scenario() -> None:
    with chargeur.connexion() as conn, conn.cursor() as cur:
        for date_iso in DATES_SCENARIO:
            cur.execute(
                f"delete from source.{TABLE} where date_extraction = %s", (_mmddyyyy(date_iso),)
            )
            cur.execute(f"delete from quarantaine.{TABLE} where rejet_partition = %s", (date_iso,))
            cur.execute(
                f"delete from source.{TABLE_2} where date_extraction = %s", (_mmddyyyy(date_iso),)
            )
            cur.execute(
                f"delete from quarantaine.{TABLE_2} where rejet_partition = %s", (date_iso,)
            )


def test_charger_scenario_agregats_et_ordre_chronologique(tmp_path: Path, monkeypatch) -> None:
    _nettoyer_scenario()
    try:
        for date_iso in DATES_SCENARIO:
            (tmp_path / f"source.{TABLE}" / date_iso).mkdir(parents=True)
            _ecrire_csv(
                tmp_path / f"source.{TABLE}" / date_iso / f"{TABLE}.csv",
                [_ligne(f"SC{date_iso[-2:]}", date_iso)],
            )

        # creances absente sur la seconde date : table absente sur une date.
        (tmp_path / f"source.{TABLE_2}" / DATES_SCENARIO[0]).mkdir(parents=True)
        with (tmp_path / f"source.{TABLE_2}" / DATES_SCENARIO[0] / f"{TABLE_2}.csv").open(
            "w", newline="", encoding="utf-8"
        ) as f:
            ecrivain = csv.DictWriter(f, fieldnames=COLONNES_2)
            ecrivain.writeheader()
            ecrivain.writerow(_ligne_creances("SCC01", DATES_SCENARIO[0]))

        appels: list[tuple[str, str]] = []
        original = chargeur.charger_table_partition

        def espion(table, date_iso, chemin_csv):
            appels.append((table, date_iso))
            return original(table, date_iso, chemin_csv)

        monkeypatch.setattr(chargeur, "charger_table_partition", espion)
        agregats = chargeur.charger_scenario(tmp_path, tables=[TABLE, TABLE_2])

        assert agregats[TABLE] == {
            "lues": 2,
            "inserees": 2,
            "rejetees": 0,
            "charge": 2,
            "bloque_seuil": 0,
            "en_tete_invalide": 0,
        }
        assert agregats[TABLE_2] == {
            "lues": 1,
            "inserees": 1,
            "rejetees": 0,
            "charge": 1,
            "bloque_seuil": 0,
            "en_tete_invalide": 0,
        }

        appels_relances = [date for table, date in appels if table == TABLE]
        assert appels_relances == sorted(appels_relances)
    finally:
        _nettoyer_scenario()
