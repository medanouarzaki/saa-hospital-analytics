"""Contrôles bloquants sur la table des rendez-vous (generator/rendez_vous.py).

La génération complète dure quelques secondes : tous les tests s'exécutent sur cette
génération complète, réutilisée via une fixture de portée module, plutôt que sur un
échantillon. Plusieurs propriétés (bijection avec les épisodes, jours ouverts, ordre des
dates) portent explicitement sur la totalité des lignes.
"""

import csv
import statistics
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
import yaml

from generator import (
    alea,
    config,
    ecriture,
    nomenclatures,
    parcours,
    patients,
    registre,
    temporel,
    volumes,
)
from generator import rendez_vous as rdv

TABLE = "source.rendez_vous"
GRAINE = 1

PILOTES = {
    "H": "admissions_annuelles",
    "C": "consultations_specialisees_externes",
    "U": "passages_urgences_par_jour",
}

RACINE = Path(__file__).resolve().parent.parent


def entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def comptes_par_categorie(entrees: dict[str, dict]) -> dict[str, dict[date, int]]:
    return {cat: volumes.comptes_journaliers(nom, entrees=entrees) for cat, nom in PILOTES.items()}


def patient_id_de(n_ipp: str) -> int:
    return int(n_ipp.split("-")[1])


@pytest.fixture(scope="module")
def generation(tmp_path_factory) -> dict:
    entrees = entrees_config()
    rng = alea.construire_generateur(GRAINE)
    comptes = comptes_par_categorie(entrees)
    episodes, population = parcours.construire_parcours(comptes, rng, entrees=entrees)
    lignes = rdv.generer_lignes(episodes, population, rng, entrees=entrees)

    racine = tmp_path_factory.mktemp("rdv_generation")
    execution = ecriture.Execution(
        racine,
        "scenario_30",
        GRAINE,
        entrees["date_debut"]["valeur"],
        entrees["date_fin"]["valeur"],
    )
    execution.ecrire_table(TABLE, lignes)

    return {
        "entrees": entrees,
        "episodes": episodes,
        "population": population,
        "lignes": lignes,
        "execution": execution,
        "racine": racine,
    }


def lire_entete(chemin_csv: Path) -> list[str]:
    with chemin_csv.open(encoding="utf-8") as f:
        return next(csv.reader(f))


def test_entetes_exactement_les_colonnes_du_registre(generation: dict) -> None:
    colonnes_attendues = registre.colonnes_table(TABLE)
    execution: ecriture.Execution = generation["execution"]

    premier_csv = execution.racine / next(
        relatif for relatif in execution.partitions[TABLE] if relatif.endswith(".csv")
    )
    entete = lire_entete(premier_csv)

    assert entete == colonnes_attendues


def test_conformite_nomenclatures_toutes_colonnes_codees(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    correspondance = entrees["correspondance_colonnes_nomenclatures"]["valeur"]
    colonnes_codees = [c for c in correspondance if c["table"] == TABLE]
    assert len(colonnes_codees) == 9, "le nombre de colonnes codées attendu a changé"

    for correspondance_colonne in colonnes_codees:
        colonne = correspondance_colonne["colonne"]
        nom_nomenclature = nomenclatures.nomenclature_colonne(TABLE, colonne, entrees)
        codes_valides = set(nomenclatures.codes_nomenclature(nom_nomenclature, entrees))

        valeurs_observees = {ligne[colonne] for ligne in lignes if ligne[colonne] is not None}
        hors_nomenclature = valeurs_observees - codes_valides
        assert not hors_nomenclature, (
            f"{colonne} : valeurs hors nomenclature {nom_nomenclature} : {hors_nomenclature}"
        )


def test_bijection_avec_episodes_consultation(generation: dict) -> None:
    episodes = generation["episodes"]
    lignes = generation["lignes"]

    n_consultations_attendu = sum(1 for e in episodes if e["categorie"] == "C")
    honores = [ligne for ligne in lignes if ligne["etat"] == "HO"]

    assert len(honores) == n_consultations_attendu
    assert all(not ligne["rdv_supplementaire"] for ligne in honores)

    n_ipp_honores = Counter(ligne["n_ipp"] for ligne in honores)
    # chaque episode de consultation a un rendez-vous honore et un seul : le nombre de
    # rendez-vous honores par n_ipp ne doit jamais depasser le nombre d'episodes de
    # consultation de ce meme patient
    n_consultations_par_patient = Counter(
        e["patient_id"] for e in episodes if e["categorie"] == "C"
    )
    for n_ipp, effectif in n_ipp_honores.items():
        pid = patient_id_de(n_ipp)
        assert effectif == n_consultations_par_patient[pid]


def test_taux_absence_et_annulation(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    taux_absenteisme_par_specialite = entrees["taux_absenteisme_par_specialite"]["valeur"]
    taux_annulation = entrees["taux_annulation"]["valeur"]

    # tolerances mesurees sur 3 graines independantes : ecart maximal observe 0,0078
    # (absenteisme par specialite) et 0,00005 (annulation globale)
    TOLERANCE = 0.02

    for activite, taux_attendu in taux_absenteisme_par_specialite.items():
        sous_ensemble = [
            ligne
            for ligne in lignes
            if ligne["activite"] == activite and ligne["etat"] in ("HO", "CO")
        ]
        n_absences = sum(1 for ligne in sous_ensemble if ligne["etat"] == "CO")
        part = n_absences / len(sous_ensemble)
        assert abs(part - taux_attendu) < TOLERANCE, (activite, taux_attendu, part)

    sous_ensemble_annulation = [ligne for ligne in lignes if ligne["etat"] in ("HO", "CO", "AN")]
    n_annulations = sum(1 for ligne in sous_ensemble_annulation if ligne["etat"] == "AN")
    part_annulation = n_annulations / len(sous_ensemble_annulation)
    assert abs(part_annulation - taux_annulation) < TOLERANCE, (taux_annulation, part_annulation)


def test_pente_absenteisme_reelle(generation: dict) -> None:
    entrees = generation["entrees"]

    # verifie le mecanisme lui-meme (generator/rendez_vous.py::_delai_biaise_longue_attente)
    # plutot qu'un decompte agrege sur la generation complete : un decoupage global en
    # tranches de delai (ex. court/long en jours absolus) melange les specialites, dont les
    # medianes vont de 5 a 45 jours, et le simple melange des specialites peut reproduire
    # l'ordre attendu meme sans pente reelle -- mesure du lot, voir mutation ci-dessous.
    # Comparer les tirages de la fonction biaisee a ceux de la loi log-normale non biaisee
    # au meme parametre isole proprement l'effet de la pente.
    rng_biaise = alea.construire_generateur(GRAINE)
    rng_neutre = alea.construire_generateur(GRAINE)
    mediane = 20.0
    ecart_type_log = entrees["ecart_type_log_delai"]["valeur"]
    pente = entrees["pente_absenteisme_delai"]["valeur"]

    N = 5000
    delais_biaises = [
        rdv._delai_biaise_longue_attente(mediane, ecart_type_log, pente, rng_biaise)
        for _ in range(N)
    ]
    delais_neutres = [rdv._delai_lognormal(mediane, ecart_type_log, rng_neutre) for _ in range(N)]

    moyenne_biaisee = sum(delais_biaises) / N
    moyenne_neutre = sum(delais_neutres) / N

    assert moyenne_biaisee > moyenne_neutre, (moyenne_biaisee, moyenne_neutre)


def test_delai_median_par_activite(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    population = generation["population"]

    delais_medians_attendus = entrees["delai_rdv_par_specialite"]["valeur"]
    date_creation_par_patient = {p["patient_id"]: p["date_creation"] for p in population}

    honores = [ligne for ligne in lignes if ligne["etat"] == "HO"]

    # eligibles : le patient existait deja la veille du rendez-vous ou avant. Les
    # rendez-vous dont le patient est cree le jour meme (fiche ouverte a la premiere
    # visite) n'ont structurellement aucun delai possible et ne relevent pas de
    # delai_rdv_par_specialite ; mesure : 59,7 % des episodes de consultation tombent
    # dans ce cas structurel.
    def marge_disponible(ligne: dict) -> int:
        pid = patient_id_de(ligne["n_ipp"])
        return (ligne["date_rendez_vous"].date() - date_creation_par_patient[pid]).days

    eligibles = [ligne for ligne in honores if marge_disponible(ligne) > 0]

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 10 jours
    # (ophtalmologie, mediane 45 j), du a l'ecretage du delai tire a la marge de jours
    # reellement disponible avant le rendez-vous (voir generator/rendez_vous.py) ; plus
    # marque pour les medianes les plus hautes.
    TOLERANCE_JOURS = 12
    for activite, mediane_attendue in delais_medians_attendus.items():
        delais = [
            (ligne["date_rendez_vous"].date() - ligne["date_creation"].date()).days
            for ligne in eligibles
            if ligne["activite"] == activite
        ]
        assert len(delais) > 0
        mediane_mesuree = statistics.median(delais)
        assert abs(mediane_mesuree - mediane_attendue) < TOLERANCE_JOURS, (
            activite,
            mediane_attendue,
            mediane_mesuree,
        )


def test_part_rdv_jour_meme(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    population = generation["population"]

    part_attendue = entrees["part_rdv_jour_meme"]["valeur"]
    date_creation_par_patient = {p["patient_id"]: p["date_creation"] for p in population}

    honores = [ligne for ligne in lignes if ligne["etat"] == "HO"]

    def marge_disponible(ligne: dict) -> int:
        pid = patient_id_de(ligne["n_ipp"])
        return (ligne["date_rendez_vous"].date() - date_creation_par_patient[pid]).days

    eligibles = [ligne for ligne in honores if marge_disponible(ligne) > 0]

    n_jour_meme = sum(
        1
        for ligne in eligibles
        if ligne["date_rendez_vous"].date() == ligne["date_creation"].date()
    )
    part_mesuree = n_jour_meme / len(eligibles)

    # tolerance mesuree sur 3 graines independantes : ecart maximal observe 0,0032
    TOLERANCE = 0.02
    assert abs(part_mesuree - part_attendue) < TOLERANCE, (part_attendue, part_mesuree)


def test_patients_adresses(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    part_attendue = entrees["part_patients_adresses"]["valeur"]

    with (RACINE / "docs" / "observation" / "releve_champs.yml").open(encoding="utf-8") as f:
        releve = yaml.safe_load(f)
    champ_origine = next(
        champ
        for ecran in releve["ecrans"]
        for champ in ecran["champs"]
        if champ["id"] == "REL-RDV.R03"
    )
    code_adresse_attendu = champ_origine["valeurs_observees"][0]

    n_adresses = sum(1 for ligne in lignes if ligne["origine"] == code_adresse_attendu)
    part_mesuree = n_adresses / len(lignes)

    # tolerance mesuree sur 3 graines independantes de mesure_tolerances_rdv2.py :
    # ecart maximal observe 0,0062 sur un parametre distinct mais de meme nature
    TOLERANCE = 0.02
    assert abs(part_mesuree - part_attendue) < TOLERANCE, (part_attendue, part_mesuree)


def test_ordre_des_dates(generation: dict) -> None:
    lignes = generation["lignes"]
    population = generation["population"]
    date_creation_par_patient = {p["patient_id"]: p["date_creation"] for p in population}

    assert len(lignes) > 0
    for ligne in lignes:
        assert ligne["date_creation"].date() <= ligne["date_rendez_vous"].date(), ligne
        pid = patient_id_de(ligne["n_ipp"])
        assert date_creation_par_patient[pid] <= ligne["date_creation"].date(), ligne


def test_jours_ouverts(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    n_fermes = 0
    for ligne in lignes:
        if temporel.poids_jour(ligne["date_creation"].date(), "programme", entrees) <= 0:
            n_fermes += 1
        if temporel.poids_jour(ligne["date_rendez_vous"].date(), "programme", entrees) <= 0:
            n_fermes += 1
    assert n_fermes == 0


def test_debordement_de_periode(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    debordement = [ligne for ligne in lignes if ligne["date_rendez_vous"].date() > date_fin]

    assert len(debordement) > 0
    assert all(ligne["etat"] == "EI" for ligne in debordement)
    assert all(ligne["rdv_supplementaire"] for ligne in debordement)


def test_horodatages_non_triviaux(generation: dict) -> None:
    # part de minuit attendue sous un tirage horaire reel : le profil horaire "programme"
    # porte un poids nul aux heures 0-7 (voir generator/config/temporel.yml), donc minuit
    # (heure 0) ne peut structurellement jamais etre tire : seuil pose a 0,01, tres
    # au-dessus de zero pour ne pas etre fragile, tres en-deca d'un horodatage trivial
    # (100 % a minuit, mesure du lot de correction sur date_modification avant fix).
    SEUIL_PART_MINUIT = 0.01

    import yaml as _yaml

    with (RACINE / "docs" / "champs" / "registre_champs.yml").open(encoding="utf-8") as f:
        registre_brut = _yaml.safe_load(f)

    colonnes_horodatage = [
        (e["table"], e["colonne"]) for e in registre_brut if e["type_metier"] == "horodatage"
    ]

    tables_produites = {
        "source.patients": generation_patients()["lignes"],
        TABLE: generation["lignes"],
    }

    for table, colonne in colonnes_horodatage:
        if table not in tables_produites:
            continue
        lignes_table = tables_produites[table]
        valeurs = [ligne[colonne] for ligne in lignes_table if ligne.get(colonne) is not None]
        if not valeurs:
            continue
        n_minuit = sum(1 for v in valeurs if v.hour == 0 and v.minute == 0 and v.second == 0)
        part_minuit = n_minuit / len(valeurs)
        assert part_minuit < SEUIL_PART_MINUIT, (table, colonne, part_minuit)


_CACHE_GENERATION_PATIENTS: dict = {}


def generation_patients() -> dict:
    if not _CACHE_GENERATION_PATIENTS:
        entrees = entrees_config()
        rng = alea.construire_generateur(GRAINE)
        comptes = comptes_par_categorie(entrees)
        episodes, population = parcours.construire_parcours(comptes, rng, entrees=entrees)
        lignes = patients.generer_lignes(episodes, population, rng, entrees=entrees)
        _CACHE_GENERATION_PATIENTS["lignes"] = lignes
    return _CACHE_GENERATION_PATIENTS


def test_reproductibilite_deux_graines_deux_formats(generation: dict) -> None:
    entrees = generation["entrees"]

    def executer(graine: int, racine: Path) -> ecriture.Execution:
        rng = alea.construire_generateur(graine)
        comptes = comptes_par_categorie(entrees)
        episodes, population = parcours.construire_parcours(comptes, rng, entrees=entrees)
        lignes = rdv.generer_lignes(episodes, population, rng, entrees=entrees)
        execution = ecriture.Execution(
            racine,
            "scenario_30",
            graine,
            entrees["date_debut"]["valeur"],
            entrees["date_fin"]["valeur"],
        )
        execution.ecrire_table(TABLE, lignes)
        return execution

    racine_a1 = generation["racine"].parent / "repro_rdv_a1"
    racine_a2 = generation["racine"].parent / "repro_rdv_a2"
    racine_b = generation["racine"].parent / "repro_rdv_b"

    execution_a1 = executer(7, racine_a1)
    execution_a2 = executer(7, racine_a2)
    execution_b = executer(8, racine_b)

    empreintes_a1_csv = {k: v for k, v in execution_a1.empreintes.items() if k.endswith(".csv")}
    empreintes_a2_csv = {k: v for k, v in execution_a2.empreintes.items() if k.endswith(".csv")}
    empreintes_a1_parquet = {
        k: v for k, v in execution_a1.empreintes.items() if k.endswith(".parquet")
    }
    empreintes_a2_parquet = {
        k: v for k, v in execution_a2.empreintes.items() if k.endswith(".parquet")
    }

    assert empreintes_a1_csv == empreintes_a2_csv
    assert empreintes_a1_parquet == empreintes_a2_parquet

    empreintes_b_csv = {k: v for k, v in execution_b.empreintes.items() if k.endswith(".csv")}
    # controle positif : une graine differente doit produire des empreintes differentes
    assert empreintes_a1_csv != empreintes_b_csv
