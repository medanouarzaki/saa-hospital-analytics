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

import numpy as np
import pytest
import yaml

from generator import ecriture, patients, registre

TABLE = "source.patients"


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
def generation(generation_partagee: dict) -> dict:
    partagee = generation_partagee
    return {
        "entrees": partagee["entrees"],
        "episodes": partagee["episodes"],
        "population": partagee["population"],
        "lignes": partagee["lignes"][TABLE],
        "execution": partagee["execution"],
        "racine": partagee["racine"],
    }


def toutes_les_lignes_csv(execution: ecriture.Execution) -> list[dict]:
    lignes: list[dict] = []
    for relatif in execution.partitions[TABLE]:
        if not relatif.endswith(".csv"):
            continue
        chemin = execution.racine / relatif
        with chemin.open(encoding="utf-8") as f:
            lignes.extend(csv.DictReader(f))
    return lignes


def _charger_verite_terrain(execution: ecriture.Execution) -> dict:
    chemin = execution.racine / execution.scenario / "verite_terrain.yml"
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


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

    vt = _charger_verite_terrain(generation["execution"])
    entrees_ages = vt["ages_incoherents"]["entrees"]
    n_ipp_exemptes = {entree["identifiant"] for entree in entrees_ages}
    assert len(n_ipp_exemptes) == vt["ages_incoherents"]["decompte"]

    n_ipp_verifies = 0
    for ligne in lignes:
        if ligne["n_ipp"] in n_ipp_exemptes:
            continue
        n_ipp_verifies += 1
        assert ligne["date_naissance"] < ligne["date_attribution"], ligne
        if ligne["date_modification"] is not None:
            assert ligne["date_modification"].date() > ligne["date_attribution"], ligne
    assert n_ipp_verifies > 0


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
    vt = _charger_verite_terrain(generation["execution"])
    n_ipp_ages_exemptes = {entree["identifiant"] for entree in vt["ages_incoherents"]["entrees"]}
    assert len(n_ipp_ages_exemptes) == vt["ages_incoherents"]["decompte"]

    n_mineurs_veufs = 0
    for ligne in lignes:
        if ligne["n_ipp"] in n_ipp_ages_exemptes:
            continue
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
    taux_champs_manquants = entrees["taux_champs_manquants"]["valeur"]
    # tolerance mesuree sur 5 graines independantes : ecart maximal observe 0,0056
    TOLERANCE = 0.02
    for colonne, taux in taux_attendu.items():
        # email, telephone_2 et profession recoivent en plus une absence injectee
        # (generator/defauts.py) au-dela de l'absence structurelle mesuree ici : leur taux
        # de presence final est gouverne par taux_champs_manquants, pas par ce parametre.
        if colonne in taux_champs_manquants:
            taux = 1 - taux_champs_manquants[colonne]
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


def test_repartition_type_modification_complete(generation: dict) -> None:
    entrees = generation["entrees"]
    execution_obj = generation["execution"]

    repartition = entrees["repartition_type_modification"]["valeur"]
    assert abs(sum(repartition.values()) - 1.0) < 1e-9
    assert set(repartition) == set(patients.COLONNES_PAR_TYPE_MODIFICATION)

    vt = _charger_verite_terrain(execution_obj)
    assert vt["fiches_modifiees"]["decompte"] > 0
    types_presents = {entree["type_modification"] for entree in vt["fiches_modifiees"]["entrees"]}
    assert types_presents == set(repartition), (
        "chaque type configuré doit apparaître dans la génération partagée"
    )


def test_version_en_vigueur_cas_aux_bornes() -> None:
    v1 = {"date_extraction": date(2024, 1, 10), "valeur": "premiere"}
    v2 = {"date_extraction": date(2024, 3, 1), "valeur": "deuxieme"}
    versions = [v2, v1]  # ordre volontairement inverse : la fonction doit trier elle-même

    # avant la premiere version : repli sur la premiere (meilleure information disponible)
    assert patients.version_en_vigueur(versions, date(2023, 6, 1)) is v1

    # exactement a la date_extraction de la premiere : cette version est en vigueur
    assert patients.version_en_vigueur(versions, date(2024, 1, 10)) is v1

    # entre les deux : la premiere reste en vigueur, la deuxieme n'a pas encore ete extraite
    assert patients.version_en_vigueur(versions, date(2024, 2, 1)) is v1

    # exactement a la date_extraction de la deuxieme : elle devient en vigueur
    assert patients.version_en_vigueur(versions, date(2024, 3, 1)) is v2

    # apres la derniere version
    assert patients.version_en_vigueur(versions, date(2024, 6, 1)) is v2
