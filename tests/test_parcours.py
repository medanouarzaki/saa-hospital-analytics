"""Contrôles bloquants sur le fil des épisodes (generator/parcours.py)."""

import subprocess
import sys
from collections import Counter
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

    # la file préexistante est structurellement les tout premiers identifiants
    # (ajoutés avant le fil des épisodes) ; des patients nouveaux dont la fiche est
    # créée à la prise d'un rendez-vous peuvent aussi porter une date de création
    # antérieure au début de la période (cas limite explicite), sans appartenir à la
    # file préexistante — les deux ne se distinguent plus par la seule date.
    prealables = sorted(population, key=lambda p: p["patient_id"])[:effectif_configure]
    assert all(p["activite_creation"] is None for p in prealables)
    assert len(prealables) == effectif_configure

    for patient in prealables:
        assert patient["date_creation"] < date_debut
        anciennete = (date_debut - patient["date_creation"]).days
        assert anciennete <= anciennete_max


def test_part_patients_connus() -> None:
    entrees = entrees_config()
    part_configuree = entrees["part_patients_connus"]["valeur"]
    episodes, _ = construire(1, entrees)

    # un épisode est « connu » s'il n'est pas le tout premier épisode de son patient :
    # la date de création de la fiche ne distingue plus connu de nouveau depuis que la
    # fiche d'un nouveau patient de consultation peut être créée avant l'épisode lui-même.
    premiers: dict[int, dict] = {}
    for episode in episodes:
        premiers.setdefault(episode["patient_id"], episode)
    connus = sum(1 for e in episodes if premiers[e["patient_id"]] is not e)
    part_mesuree = connus / len(episodes)

    # Tolérance mesurée sur cinq graines (rapport.md) : écart maximal observé 0,0017.
    # Seuil fixé à 0,005, au-dessus de l'écart mesuré.
    tolerance = 0.005
    assert abs(part_mesuree - part_configuree) < tolerance


def test_croissance_identifiants() -> None:
    entrees = entrees_config()
    _, population = construire(1, entrees)

    # les identifiants sont attribués dans l'ordre d'attribution du fil des épisodes,
    # de façon strictement croissante et sans doublon. La date de création n'est plus
    # nécessairement croissante avec l'identifiant depuis que la fiche d'un nouveau
    # patient de consultation peut être créée avant l'épisode qui l'a fait naître
    # (parfois avant celle d'un patient d'identifiant inférieur) : ce n'est plus
    # l'invariant vérifié ici.
    tries_par_id = sorted(population, key=lambda p: p["patient_id"])
    ids = [p["patient_id"] for p in tries_par_id]

    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert ids == list(range(len(ids)))


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


def test_invariance_fil_episodes_par_categorie_et_patients() -> None:
    # le mecanisme deplace des dates de creation de fiche, il ne refait pas le fil : le nombre
    # d'episodes par categorie et le nombre de patients distincts doivent rester ceux que
    # produit le module de volumes, independamment de la deuxieme passe qui deplace les
    # dates de creation des fiches ouvertes a la prise d'un rendez-vous.
    entrees = entrees_config()
    comptes = comptes_par_categorie(entrees)
    episodes, population = construire(1, entrees)

    attendu_par_categorie = {cat: sum(c.values()) for cat, c in comptes.items()}
    mesure_par_categorie = Counter(e["categorie"] for e in episodes)

    for categorie, attendu in attendu_par_categorie.items():
        assert mesure_par_categorie[categorie] == attendu, categorie

    identifiants = {p["patient_id"] for p in population}
    assert len(identifiants) == len(population)


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
