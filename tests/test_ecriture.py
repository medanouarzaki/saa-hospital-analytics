"""Contrôles bloquants sur le socle d'écriture (generator/ecriture.py)."""

import csv
import hashlib
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yaml

from generator import config, ecriture, registre

TABLE = "source.relances"


def ligne_valide(date_extraction: date) -> dict:
    return {
        "n_relance": "1",
        "n_creance": "10",
        "date_relance": date(2024, 1, 5),
        "canal": "SMS",
        "resultat": "sans_effet",
        "date_extraction": date_extraction,
    }


def nouvelle_execution(racine: Path) -> ecriture.Execution:
    return ecriture.Execution(racine, "scenario_30", 1, "2024-01-01", "2024-01-02")


def seul_csv(racine: Path) -> Path:
    return next(racine.rglob("*.csv"))


def test_entetes_exactement_les_colonnes_du_registre(tmp_path: Path) -> None:
    colonnes = registre.colonnes_table(TABLE)
    execution = nouvelle_execution(tmp_path)
    execution.ecrire_table(TABLE, [ligne_valide(date(2024, 1, 10))])

    with seul_csv(tmp_path).open(encoding="utf-8") as f:
        entete = f.readline().rstrip("\n").split(",")

    assert entete == colonnes


def test_colonne_manquante_et_colonne_en_trop(tmp_path: Path) -> None:
    execution = nouvelle_execution(tmp_path)

    ligne_incomplete = ligne_valide(date(2024, 1, 10))
    del ligne_incomplete["canal"]
    try:
        execution.ecrire_table(TABLE, [ligne_incomplete])
        raise AssertionError("une colonne manquante aurait dû être rejetée")
    except ValueError as erreur:
        assert "canal" in str(erreur)

    ligne_en_trop = ligne_valide(date(2024, 1, 10))
    ligne_en_trop["colonne_inconnue"] = "x"
    try:
        execution.ecrire_table(TABLE, [ligne_en_trop])
        raise AssertionError("une colonne en trop aurait dû être rejetée")
    except ValueError as erreur:
        assert "colonne_inconnue" in str(erreur)


def test_type_non_traite(monkeypatch, tmp_path: Path) -> None:
    original = registre.type_metier

    def type_metier_mute(table: str, colonne: str, chemin=registre.CHEMIN_REGISTRE):
        if colonne == "canal":
            return "type_inconnu"
        return original(table, colonne, chemin)

    monkeypatch.setattr(registre, "type_metier", type_metier_mute)

    execution = nouvelle_execution(tmp_path)
    try:
        execution.ecrire_table(TABLE, [ligne_valide(date(2024, 1, 10))])
        raise AssertionError("un type_metier sans règle aurait dû faire échouer l'écriture")
    except ValueError as erreur:
        assert "type_inconnu" in str(erreur)


def test_mise_en_forme_dates_et_horodatages() -> None:
    format_config = {e["nom"]: e for e in config.charger_entrees()}
    gabarit_date = format_config["format_date"]["valeur"]
    gabarit_horodatage = format_config["format_horodatage"]["valeur"]

    jour = date(2024, 3, 7)
    instant = datetime(2024, 3, 7, 9, 5, 30)

    assert ecriture.mettre_en_forme(jour, "date", format_config) == jour.strftime(gabarit_date)
    assert ecriture.mettre_en_forme(instant, "horodatage", format_config) == instant.strftime(
        gabarit_horodatage
    )


def test_partitionnement_par_date_extraction(tmp_path: Path) -> None:
    execution = nouvelle_execution(tmp_path)
    dates = [date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 10), date(2024, 1, 12)]
    execution.ecrire_table(TABLE, [ligne_valide(d) for d in dates])

    dates_distinctes = len(set(dates))
    fichiers_csv = list(tmp_path.rglob("*.csv"))
    assert len(fichiers_csv) == dates_distinctes

    for chemin in fichiers_csv:
        with chemin.open(encoding="utf-8") as f:
            lignes_fichier = f.readlines()
        assert len(lignes_fichier) > 1


def test_conservation_lignes_et_identifiants(tmp_path: Path) -> None:
    execution = nouvelle_execution(tmp_path)
    dates = [date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 10)]
    lignes = [{**ligne_valide(d), "n_relance": str(i)} for i, d in enumerate(dates)]
    execution.ecrire_table(TABLE, lignes)

    total_lignes = 0
    identifiants_lus = set()
    for chemin in tmp_path.rglob("*.csv"):
        with chemin.open(encoding="utf-8") as f:
            for ligne in csv.DictReader(f):
                total_lignes += 1
                identifiants_lus.add(ligne["n_relance"])

    assert total_lignes == len(lignes)
    assert identifiants_lus == {ligne["n_relance"] for ligne in lignes}


def test_les_deux_formats_portent_le_meme_contenu(tmp_path: Path) -> None:
    execution = nouvelle_execution(tmp_path)
    execution.ecrire_table(TABLE, [ligne_valide(date(2024, 1, 10))])

    chemin_csv = seul_csv(tmp_path)
    chemin_parquet = chemin_csv.with_suffix(".parquet")

    df_csv = pd.read_csv(chemin_csv, dtype=str, keep_default_na=False)
    df_parquet = pd.read_parquet(chemin_parquet)

    assert list(df_csv.columns) == list(df_parquet.columns)
    for colonne in df_csv.columns:
        assert df_csv[colonne].tolist() == df_parquet[colonne].astype(str).tolist()


def test_manifeste_recense_partitions_et_empreintes(tmp_path: Path) -> None:
    execution = nouvelle_execution(tmp_path)
    dates = [date(2024, 1, 10), date(2024, 1, 11)]
    execution.ecrire_table(TABLE, [ligne_valide(d) for d in dates])
    chemin_manifeste = execution.ecrire_manifeste()

    with chemin_manifeste.open(encoding="utf-8") as f:
        manifeste = yaml.safe_load(f)

    partitions_attendues = set(execution.partitions[TABLE])
    partitions_manifeste = set(manifeste["partitions"][TABLE])
    assert partitions_manifeste == partitions_attendues

    for relatif, empreinte in manifeste["empreintes"].items():
        empreinte_recalculee = hashlib.sha256((tmp_path / relatif).read_bytes()).hexdigest()
        assert empreinte == empreinte_recalculee


def test_reproductibilite_empreintes(tmp_path: Path) -> None:
    lignes = [ligne_valide(date(2024, 1, 10))]

    execution_a = nouvelle_execution(tmp_path / "a")
    execution_a.ecrire_table(TABLE, lignes)
    execution_b = nouvelle_execution(tmp_path / "b")
    execution_b.ecrire_table(TABLE, lignes)

    assert execution_a.empreintes == execution_b.empreintes

    lignes_modifiees = [{**ligne_valide(date(2024, 1, 10)), "resultat": "autre_valeur"}]
    execution_c = nouvelle_execution(tmp_path / "c")
    execution_c.ecrire_table(TABLE, lignes_modifiees)

    assert execution_a.empreintes != execution_c.empreintes
