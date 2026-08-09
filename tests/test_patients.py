"""Contrôles bloquants sur la table des patients (generator/patients.py).

La génération complète (~24 900 patients, ~28 000 lignes) dure environ 5 s :
tous les tests s'exécutent sur cette génération complète, réutilisée via une
fixture de portée module, plutôt que sur un échantillon. Un échantillon
n'aurait pas prouvé les propriétés portant sur la totalité des lignes
(en-têtes, ordre des dates, régime d'extraction, effectif) ; le coût de la
génération complète reste modeste, rien ne justifie de l'éviter pour les
tests purement statistiques.
"""

import csv
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from generator import alea, config, ecriture, nomenclatures, parcours, patients, registre, volumes

TABLE = "source.patients"
GRAINE = 1

PILOTES = {
    "H": "admissions_annuelles",
    "C": "consultations_specialisees_externes",
    "U": "passages_urgences_par_jour",
}


def entrees_config() -> dict[str, dict]:
    return {e["nom"]: e for e in config.charger_entrees()}


def comptes_par_categorie(entrees: dict[str, dict]) -> dict[str, dict[date, int]]:
    return {cat: volumes.comptes_journaliers(nom, entrees=entrees) for cat, nom in PILOTES.items()}


def construire_episodes_population(graine: int, entrees: dict[str, dict]):
    rng = alea.construire_generateur(graine)
    comptes = comptes_par_categorie(entrees)
    return parcours.construire_parcours(comptes, rng, entrees=entrees)


def bornes_jours(tranche: str) -> tuple[int, int | None]:
    if tranche.endswith("+"):
        return int(tranche[:-1]) * 365, None
    borne_min, borne_max = (int(x) for x in tranche.split("-"))
    return borne_min * 365, borne_max * 365 + 364


def tranche_de_age_jours(age_jours: int, tranches: list[str]) -> str:
    for tranche in tranches:
        lo, hi = bornes_jours(tranche)
        if hi is None:
            if age_jours >= lo:
                return tranche
        elif lo <= age_jours <= hi:
            return tranche
    return tranches[-1]


@pytest.fixture(scope="module")
def generation(tmp_path_factory) -> dict:
    entrees = entrees_config()
    rng = alea.construire_generateur(GRAINE)
    comptes = comptes_par_categorie(entrees)
    episodes, population = parcours.construire_parcours(comptes, rng, entrees=entrees)
    lignes = patients.generer_lignes(episodes, population, rng, entrees=entrees)

    racine = tmp_path_factory.mktemp("patients_generation")
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


def toutes_les_lignes_csv(execution: ecriture.Execution) -> list[dict]:
    lignes: list[dict] = []
    for relatif in execution.partitions[TABLE]:
        if not relatif.endswith(".csv"):
            continue
        chemin = execution.racine / relatif
        with chemin.open(encoding="utf-8") as f:
            lignes.extend(csv.DictReader(f))
    return lignes


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
    assert len(colonnes_codees) == 14, "le nombre de colonnes codées attendu a changé"

    for correspondance_colonne in colonnes_codees:
        colonne = correspondance_colonne["colonne"]
        nom_nomenclature = nomenclatures.nomenclature_colonne(TABLE, colonne, entrees)
        codes_valides = set(nomenclatures.codes_nomenclature(nom_nomenclature, entrees))

        valeurs_observees = {ligne[colonne] for ligne in lignes}
        hors_nomenclature = valeurs_observees - codes_valides
        assert not hors_nomenclature, (
            f"{colonne} : valeurs hors nomenclature {nom_nomenclature} : {hors_nomenclature}"
        )


def test_effectif_recompute_independamment(generation: dict) -> None:
    population = generation["population"]
    lignes = generation["lignes"]

    effectif_attendu = len({p["patient_id"] for p in population})
    ipp_distincts = {ligne["n_ipp"] for ligne in lignes}

    assert len(ipp_distincts) == effectif_attendu
    assert effectif_attendu == len(population), "identifiants de patients en double"


def test_ordre_des_dates_sur_toutes_les_lignes(generation: dict) -> None:
    lignes = generation["lignes"]
    assert len(lignes) > 0

    for ligne in lignes:
        assert ligne["date_naissance"] < ligne["date_attribution"], ligne
        if ligne["date_modification"] is not None:
            assert ligne["date_modification"] > ligne["date_attribution"], ligne


def test_structure_age_ponderee_par_categorie(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    episodes = generation["episodes"]
    population = generation["population"]

    structure = entrees["structure_age"]["valeur"]
    tranches = structure["tranches"]
    parts_base = np.array(structure["parts"], dtype=float)
    profils = entrees["profil_recours_demographique"]["valeur"]

    premiers = patients._premier_episode_par_patient(episodes)
    compte_categorie: Counter = Counter()
    for p in population:
        premier = premiers.get(p["patient_id"])
        compte_categorie[premier["categorie"] if premier else None] += 1
    total_population = sum(compte_categorie.values())

    attendu = np.zeros(len(tranches))
    for categorie, effectif in compte_categorie.items():
        if categorie is None or categorie not in profils:
            contribution = parts_base
        else:
            multiplicateurs = np.array([profils[categorie][t] for t in tranches])
            contribution = parts_base * multiplicateurs
            contribution = contribution / contribution.sum()
        attendu += (effectif / total_population) * contribution

    par_patient = {}
    for ligne in lignes:
        par_patient.setdefault(ligne["n_ipp"], ligne)

    compte_observe: Counter = Counter()
    for ligne in par_patient.values():
        age_jours = (ligne["date_attribution"] - ligne["date_naissance"]).days
        compte_observe[tranche_de_age_jours(age_jours, tranches)] += 1
    total_observe = sum(compte_observe.values())
    observe = np.array([compte_observe.get(t, 0) / total_observe for t in tranches])

    # tolérance mesurée sur 5 graines indépendantes : écart maximal observé 0,0056
    TOLERANCE = 0.02
    ecart_max = np.max(np.abs(observe - attendu))
    assert ecart_max < TOLERANCE, (tranches, attendu.tolist(), observe.tolist())


def test_repartition_couverture_nom_impose(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    couverture_attendue = entrees["repartition_couverture"]["valeur"]

    par_patient = {}
    for ligne in lignes:
        par_patient.setdefault(ligne["n_ipp"], ligne)

    compte_observe = Counter(ligne["compagnie_assurance"] for ligne in par_patient.values())
    total = sum(compte_observe.values())

    # tolérance mesurée sur 5 graines indépendantes : écart maximal observé 0,0044
    TOLERANCE = 0.02
    for code, part_attendue in couverture_attendue.items():
        part_observee = compte_observe.get(code, 0) / total
        assert abs(part_observee - part_attendue) < TOLERANCE, (code, part_attendue, part_observee)


def test_profil_recours_ordre_directionnel(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    episodes = generation["episodes"]

    profils = entrees["profil_recours_demographique"]["valeur"]
    # H (hospitalisation) surreprésente 0-4 (multiplicateur 1,6) bien plus que C
    # (consultation, multiplicateur 0,7) : la part de la tranche 0-4 doit donc être
    # strictement plus élevée chez les patients dont le premier épisode est H que
    # chez ceux dont le premier épisode est C.
    assert profils["H"]["0-4"] > profils["C"]["0-4"]

    premiers = patients._premier_episode_par_patient(episodes)
    par_patient = {}
    for ligne in lignes:
        par_patient.setdefault(ligne["n_ipp"], ligne)

    def part_0_4(categorie: str) -> float:
        n_0_4 = 0
        n_total = 0
        for pid, premier in premiers.items():
            if premier["categorie"] != categorie:
                continue
            ligne = par_patient.get(f"IPP-{pid:06d}")
            if ligne is None:
                continue
            age_jours = (ligne["date_attribution"] - ligne["date_naissance"]).days
            n_total += 1
            if age_jours < 5 * 365:
                n_0_4 += 1
        assert n_total > 0
        return n_0_4 / n_total

    assert part_0_4("H") > part_0_4("C")


def test_regime_extraction(generation: dict) -> None:
    entrees = generation["entrees"]
    population = generation["population"]
    lignes = generation["lignes"]
    execution: ecriture.Execution = generation["execution"]

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])

    effectif_prealable_attendu = sum(1 for p in population if p["date_creation"] < date_debut)
    ipp_prealables = {
        f"IPP-{p['patient_id']:06d}" for p in population if p["date_creation"] < date_debut
    }

    chemin_premiere_partition = execution.racine / next(
        relatif
        for relatif in execution.partitions[TABLE]
        if relatif.endswith(".csv") and relatif.split("/")[-2] == date_debut.isoformat()
    )
    with chemin_premiere_partition.open(encoding="utf-8") as f:
        lignes_premiere_partition = list(csv.DictReader(f))

    prealables_dans_premiere_partition = [
        ligne for ligne in lignes_premiere_partition if ligne["n_ipp"] in ipp_prealables
    ]
    assert len(prealables_dans_premiere_partition) == effectif_prealable_attendu

    lignes_ecrites_disque = toutes_les_lignes_csv(execution)
    nb_modifications_independant = sum(
        1 for ligne in lignes_ecrites_disque if ligne["date_modification"]
    )
    total_attendu = len(population) + nb_modifications_independant

    assert len(lignes_ecrites_disque) == total_attendu
    assert execution.decompte_lignes[TABLE] == len(lignes)
    assert execution.decompte_lignes[TABLE] == total_attendu


def test_nationalite_observee_et_majoritaire(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    repartition_pays = entrees["repartition_pays"]["valeur"]
    code_majoritaire_attendu = max(repartition_pays, key=repartition_pays.get)

    compte = Counter(ligne["nationalite"] for ligne in lignes)
    total = sum(compte.values())

    assert code_majoritaire_attendu in compte
    part_majoritaire = compte[code_majoritaire_attendu] / total
    assert part_majoritaire > 0.5, (code_majoritaire_attendu, part_majoritaire, compte)


def test_reproductibilite_deux_graines_deux_formats(generation: dict) -> None:
    entrees = generation["entrees"]

    def executer(graine: int, racine: Path) -> ecriture.Execution:
        episodes, population = construire_episodes_population(graine, entrees)
        rng = alea.construire_generateur(graine)
        lignes = patients.generer_lignes(episodes, population, rng, entrees=entrees)
        execution = ecriture.Execution(
            racine,
            "scenario_30",
            graine,
            entrees["date_debut"]["valeur"],
            entrees["date_fin"]["valeur"],
        )
        execution.ecrire_table(TABLE, lignes)
        return execution

    racine_a1 = generation["racine"].parent / "repro_a1"
    racine_a2 = generation["racine"].parent / "repro_a2"
    racine_b = generation["racine"].parent / "repro_b"

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
    # contrôle positif : une graine différente doit produire des empreintes différentes,
    # sans quoi le test ne prouverait rien sur la sensibilité réelle à la graine
    assert empreintes_a1_csv != empreintes_b_csv


def test_aucune_colonne_degeneree(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    identifiants = {
        c["colonne"] for c in entrees["colonnes_identifiants"]["valeur"] if c["table"] == TABLE
    }

    par_patient = {}
    for ligne in lignes:
        par_patient.setdefault(ligne["n_ipp"], ligne)
    n_fiches = len(par_patient)

    for colonne in registre.colonnes_table(TABLE):
        valeurs_lignes = {ligne[colonne] for ligne in lignes}
        assert len(valeurs_lignes) > 1, f"{colonne} : une seule valeur distincte sur la table"

        if colonne in identifiants:
            continue
        valeurs_fiches = {ligne[colonne] for ligne in par_patient.values()}
        assert len(valeurs_fiches) < n_fiches, (
            f"{colonne} : autant de valeurs distinctes que de fiches ({n_fiches})"
        )


def test_coherence_intra_ligne(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    total = len(lignes)

    for contrainte in entrees["contraintes_coherence"]["valeur"]:
        tolerance = contrainte["tolerance"]
        nature = contrainte["nature"]

        if nature == "egalite":
            n_violations = sum(
                1
                for ligne in lignes
                if ligne[contrainte["colonne_a"]] != ligne[contrainte["colonne_b"]]
            )
        elif nature == "appartenance":
            n_violations = sum(
                1
                for ligne in lignes
                if ligne[contrainte["colonne_a"]] == contrainte["valeur_a_declenchante"]
                and ligne[contrainte["colonne_b"]] in contrainte["valeurs_b_interdites"]
            )
        elif nature == "derivation":
            table = entrees[contrainte["table_derivation"]]["valeur"]
            n_violations = sum(
                1
                for ligne in lignes
                if ligne[contrainte["colonne_b"]] != table.get(ligne[contrainte["colonne_a"]])
            )
        else:
            raise ValueError(f"nature de contrainte inconnue : {nature!r}")

        part_violations = n_violations / total
        assert part_violations <= tolerance, (
            contrainte["colonne_a"],
            contrainte["colonne_b"],
            nature,
            part_violations,
        )


def test_ordres_vraisemblance(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]

    # 1. la piece d'identite dominante chez les nationaux l'est effectivement dans la sortie
    distribution_piece = entrees["distribution_piece_identite"]["valeur"]["national"]
    code_piece_dominant = max(distribution_piece, key=distribution_piece.get)
    compte_piece = Counter(
        ligne["type_piece_identite"] for ligne in lignes if ligne["nationalite"] == "504"
    )
    assert compte_piece.most_common(1)[0][0] == code_piece_dominant

    # 2. aucune fiche mineure n'est veuve : trouve le code veuf par son libellé (controle positif
    # implicite, une KeyError ferait echouer le test si aucun libelle ne contient VEUF)
    code_veuf = next(
        couple["code"]
        for couple in entrees["nomenclature_etat_civil"]["valeur"]
        if "VEUF" in couple["libelle"].upper()
    )
    n_mineurs_veufs = 0
    for ligne in lignes:
        age_annees = (ligne["date_attribution"] - ligne["date_naissance"]).days / 365
        if age_annees < patients.AGE_MAJORITE_ANNEES and ligne["etat_civil"] == code_veuf:
            n_mineurs_veufs += 1
    assert n_mineurs_veufs == 0

    # 3. aucune fiche sans compagnie d'assurance n'est de type assure (regle deja generique au
    # test de coherence intra-ligne ; reaffirmee ici comme ordre explicite de l'etape 3)
    contrainte_assurance = next(
        c
        for c in entrees["contraintes_coherence"]["valeur"]
        if c["colonne_a"] == "compagnie_assurance"
    )
    n_violations = sum(
        1
        for ligne in lignes
        if ligne["compagnie_assurance"] == contrainte_assurance["valeur_a_declenchante"]
        and ligne["type_patient"] in contrainte_assurance["valeurs_b_interdites"]
    )
    assert n_violations == 0

    # 4. la part de deces croit avec l'age : verifie l'ordre sur chaque paire de tranches
    # consecutives, sur les fiches distinctes (l'exitus est une propriete de la fiche, pas de
    # la ligne : une fiche modifiee ne doit pas etre comptee deux fois)
    tranches = entrees["structure_age"]["valeur"]["tranches"]
    par_patient = {}
    for ligne in lignes:
        par_patient.setdefault(ligne["n_ipp"], ligne)

    parts_par_tranche = []
    for tranche in tranches:
        n_exitus = 0
        n_total = 0
        for ligne in par_patient.values():
            age_jours = (ligne["date_attribution"] - ligne["date_naissance"]).days
            if tranche_de_age_jours(age_jours, tranches) != tranche:
                continue
            n_total += 1
            if ligne["exitus"]:
                n_exitus += 1
        assert n_total > 0
        parts_par_tranche.append(n_exitus / n_total)

    for avant, apres in zip(parts_par_tranche, parts_par_tranche[1:], strict=False):
        assert apres > avant, (tranches, parts_par_tranche)


def test_matiere_du_rapprochement(generation: dict) -> None:
    lignes = generation["lignes"]

    par_patient = {}
    for ligne in lignes:
        par_patient.setdefault(ligne["n_ipp"], ligne)
    fiches = list(par_patient.values())
    n_fiches = len(fiches)

    groupes = {}
    for ligne in fiches:
        cle = (ligne["nom_famille_1"], ligne["date_naissance"])
        groupes.setdefault(cle, []).append(ligne["n_ipp"])
    couples_nom_naissance = sum(
        len(ipps) * (len(ipps) - 1) // 2 for ipps in groupes.values() if len(ipps) > 1
    )
    # mesure sur graine 1 : 549 couples ; seuil pose a 50, tres en-deca de la mesure, pour ne
    # pas rendre le test fragile a une variation de graine tout en restant strictement positif
    assert couples_nom_naissance > 50

    colonnes_identite = ["nom", "nom_famille_1", "date_naissance"]
    identites = Counter(tuple(ligne[c] for c in colonnes_identite) for ligne in fiches)
    n_uniques = sum(1 for v in identites.values() if v == 1)
    assert n_uniques < n_fiches


def test_taux_renseignement(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]
    total = len(lignes)

    taux_attendu = entrees["taux_renseignement"]["valeur"]
    # tolerance mesuree sur 5 graines independantes : ecart maximal observe 0,0056
    TOLERANCE = 0.02
    for colonne, taux in taux_attendu.items():
        n_renseigne = sum(1 for ligne in lignes if ligne[colonne] is not None)
        part = n_renseigne / total
        assert abs(part - taux) < TOLERANCE, (colonne, taux, part)


def test_tracabilite_repartie(generation: dict) -> None:
    lignes = generation["lignes"]

    valeurs_cree_par = {ligne["cree_par"] for ligne in lignes}
    assert len(valeurs_cree_par) > 1

    valeurs_modifie_par = {
        ligne["modifie_par"] for ligne in lignes if ligne["modifie_par"] is not None
    }
    assert len(valeurs_modifie_par) > 1
