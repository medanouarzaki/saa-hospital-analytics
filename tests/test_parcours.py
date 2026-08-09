"""Contrôles bloquants sur le fil des épisodes (generator/parcours.py)."""

import subprocess
import sys
from datetime import date
from pathlib import Path

from generator import alea, config, parcours, volumes

RACINE = Path(__file__).resolve().parent.parent

PILOTES = {
    "H": "admissions_annuelles",
    "C": "consultations_specialisees_externes",
    "U": "passages_urgences_par_jour",
}


def entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def comptes_par_categorie(entrees: dict[str, dict]) -> dict[str, dict[date, int]]:
    return {cat: volumes.comptes_journaliers(nom, entrees=entrees) for cat, nom in PILOTES.items()}


def construire(graine: int, entrees: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    rng = alea.construire_generateur(graine)
    comptes = comptes_par_categorie(entrees)
    return parcours.construire_parcours(comptes, rng, entrees=entrees)


def test_completude() -> None:
    entrees = entrees_config()
    episodes, _ = construire(1, entrees)

    comptes = comptes_par_categorie(entrees)
    total_attendu = sum(sum(c.values()) for c in comptes.values())

    assert len(episodes) == total_attendu


def test_chaque_episode_un_patient_existant() -> None:
    entrees = entrees_config()
    episodes, population = construire(1, entrees)

    ids_population = {p["patient_id"] for p in population}
    assert len(ids_population) == len(population), "identifiants de patients en double"

    for episode in episodes:
        assert "patient_id" in episode
        assert episode["patient_id"] in ids_population


def test_anteriorite() -> None:
    entrees = entrees_config()
    episodes, population = construire(1, entrees)
    date_creation = {p["patient_id"]: p["date_creation"] for p in population}

    for episode in episodes:
        assert episode["date"] >= date_creation[episode["patient_id"]], (
            f"épisode {episode} antérieur à la création du patient"
        )


def test_file_preexistante() -> None:
    entrees = entrees_config()
    _, population = construire(1, entrees)

    effectif_configure = entrees["effectif_file_preexistante"]["valeur"]
    anciennete_max = entrees["anciennete_maximale_file_preexistante_jours"]["valeur"]
    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])

    prealables = [p for p in population if p["date_creation"] < date_debut]
    assert len(prealables) == effectif_configure, (
        f"{len(prealables)} patients antérieurs au début de la période, "
        f"{effectif_configure} attendus"
    )

    for patient in prealables:
        assert patient["date_creation"] < date_debut
        anciennete = (date_debut - patient["date_creation"]).days
        assert anciennete <= anciennete_max


def test_part_patients_connus() -> None:
    entrees = entrees_config()
    part_configuree = entrees["part_patients_connus"]["valeur"]
    episodes, population = construire(1, entrees)

    date_creation = {p["patient_id"]: p["date_creation"] for p in population}
    connus = sum(1 for e in episodes if date_creation[e["patient_id"]] != e["date"])
    part_mesuree = connus / len(episodes)

    # Tolérance mesurée sur cinq graines (rapport.md) : écart maximal observé 0,0017.
    # Seuil fixé à 0,005, au-dessus de l'écart mesuré.
    tolerance = 0.005
    assert abs(part_mesuree - part_configuree) < tolerance


def test_croissance_identifiants() -> None:
    entrees = entrees_config()
    _, population = construire(1, entrees)

    tries_par_id = sorted(population, key=lambda p: p["patient_id"])
    dates = [p["date_creation"] for p in tries_par_id]
    ids = [p["patient_id"] for p in tries_par_id]

    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert dates == sorted(dates)


def test_determinisme() -> None:
    entrees = entrees_config()
    episodes_a, population_a = construire(7, entrees)
    episodes_b, population_b = construire(7, entrees)

    assert episodes_a == episodes_b
    assert population_a == population_b

    episodes_c, _ = construire(8, entrees)
    assert episodes_a != episodes_c


def _hash_parcours_sous_processus(graine: int) -> str:
    script = (
        "import hashlib, sys\n"
        f"sys.path.insert(0, {str(RACINE)!r})\n"
        "from generator import config, volumes, parcours, alea\n"
        "entrees = {e['nom']: e for e in config.charger_entrees()}\n"
        "pilotes = {'H': 'admissions_annuelles', 'C': 'consultations_specialisees_externes', "
        "'U': 'passages_urgences_par_jour'}\n"
        "comptes = {cat: volumes.comptes_journaliers(nom, entrees=entrees) "
        "for cat, nom in pilotes.items()}\n"
        f"rng = alea.construire_generateur({graine})\n"
        "episodes, population = parcours.construire_parcours(comptes, rng, entrees=entrees)\n"
        "texte = ''.join(f\"{e['date']}{e['categorie']}{e['patient_id']}\" for e in episodes)\n"
        "print(hashlib.sha256(texte.encode()).hexdigest())\n"
    )
    resultat = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    return resultat.stdout.strip()


def test_independance_ordre_iteration() -> None:
    entrees = entrees_config()
    episodes_a, _ = construire(9, entrees)
    episodes_b, _ = construire(9, entrees)
    texte_a = "".join(f"{e['date']}{e['categorie']}{e['patient_id']}" for e in episodes_a)
    texte_b = "".join(f"{e['date']}{e['categorie']}{e['patient_id']}" for e in episodes_b)
    assert texte_a == texte_b  # même processus : ne prouve rien seul

    hash_c = _hash_parcours_sous_processus(9)
    hash_d = _hash_parcours_sous_processus(9)
    assert hash_c == hash_d  # deux processus distincts : seule comparaison probante
