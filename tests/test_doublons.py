"""Contrôles bloquants sur l'injection des doublons d'identité (generator/doublons.py) et
sur le fichier de vérité terrain qu'elle produit (generator/verite_terrain.py).

La reconstruction indépendante de la population « avant injection » rejoue exactement la
séquence que `generator.execution.executer` exécute avant d'appeler
`generator.doublons.injecter_doublons` (même graine, même générateur dérivé) : c'est ce qui
permet de vérifier que le nombre de personnes et le fil des épisodes sont conservés, sans se
fier à un calcul qui se contenterait de soustraire le nombre de doublons de l'état déjà
transformé.
"""

from collections import Counter, defaultdict
from datetime import date

import pytest
import yaml

from generator import config, ecriture, execution, parcours, volumes

GRAINE_PARTAGEE = 1

TOLERANCE_GROUPE_VARIATION = 0.12


@pytest.fixture(scope="module")
def generation(generation_partagee: dict) -> dict:
    return generation_partagee


def _population_et_episodes_avant_injection(
    entrees: dict[str, dict], graine: int
) -> tuple[list[dict], list[dict]]:
    taux_urgences_par_jour = entrees["passages_urgences_par_jour"]["valeur"]
    rng_episodes = execution._generateur_pour(graine, 0)
    comptes = {
        cat: volumes.comptes_journaliers(
            nom,
            taux_urgences_par_jour=taux_urgences_par_jour if cat == "U" else None,
            entrees=entrees,
        )
        for cat, nom in execution.PILOTES.items()
    }
    return parcours.construire_parcours(comptes, rng_episodes, entrees=entrees)


def _charger_verite_terrain(execution_obj: ecriture.Execution) -> dict:
    chemin = execution_obj.racine / execution_obj.scenario / "verite_terrain.yml"
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _n_ipp_vers_patient_id(entrees: dict[str, dict], population: list[dict]) -> dict[str, int]:
    gabarit_ipp = entrees["gabarit_identifiant_patient"]["valeur"]
    return {gabarit_ipp.format(rang=p["patient_id"]): p["patient_id"] for p in population}


def _ligne_creation_par_ipp(lignes: list[dict]) -> dict[str, dict]:
    par_ipp = {}
    for ligne in lignes:
        if ligne["date_modification"] is None:
            par_ipp[ligne["n_ipp"]] = ligne
    return par_ipp


def test_effectif_exact_doublons(generation: dict) -> None:
    entrees = generation["entrees"]
    _, population_avant = _population_et_episodes_avant_injection(entrees, GRAINE_PARTAGEE)

    vt = _charger_verite_terrain(generation["execution"])
    paires = vt["doublons"]["paires"]

    taux = entrees["taux_doublons"]["valeur"]
    n_attendu = round(taux * len(population_avant))
    assert len(paires) == n_attendu


def test_conservation_des_personnes(generation: dict) -> None:
    entrees = generation["entrees"]
    population_apres = generation["population"]
    _, population_avant = _population_et_episodes_avant_injection(entrees, GRAINE_PARTAGEE)

    vt = _charger_verite_terrain(generation["execution"])
    n_doublons = len(vt["doublons"]["paires"])

    assert len(population_apres) - n_doublons == len(population_avant)


def test_conservation_des_episodes(generation: dict) -> None:
    entrees = generation["entrees"]
    episodes_apres = generation["episodes"]
    episodes_avant, _ = _population_et_episodes_avant_injection(entrees, GRAINE_PARTAGEE)

    assert len(episodes_apres) == len(episodes_avant)
    assert Counter(e["categorie"] for e in episodes_apres) == Counter(
        e["categorie"] for e in episodes_avant
    )

    gabarit_ipp = entrees["gabarit_identifiant_patient"]["valeur"]
    n_ipp_existants = {ligne["n_ipp"] for ligne in generation["lignes"]["source.patients"]}
    for episode in episodes_apres:
        assert gabarit_ipp.format(rang=episode["patient_id"]) in n_ipp_existants, episode


def test_nombre_de_fiches_egale_personnes_plus_doublons(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]["source.patients"]
    _, population_avant = _population_et_episodes_avant_injection(entrees, GRAINE_PARTAGEE)
    vt = _charger_verite_terrain(generation["execution"])
    n_doublons = len(vt["doublons"]["paires"])

    n_fiches = len({ligne["n_ipp"] for ligne in lignes})
    assert n_fiches == len(population_avant) + n_doublons


def test_seconde_fiche_porte_au_moins_un_episode(generation: dict) -> None:
    entrees = generation["entrees"]
    episodes = generation["episodes"]
    population = generation["population"]
    n_ipp_vers_id = _n_ipp_vers_patient_id(entrees, population)

    n_episodes_par_patient = Counter(e["patient_id"] for e in episodes)
    vt = _charger_verite_terrain(generation["execution"])
    for paire in vt["doublons"]["paires"]:
        patient_id_2 = n_ipp_vers_id[paire["n_ipp_2"]]
        assert n_episodes_par_patient.get(patient_id_2, 0) >= 1, paire


def test_chronologie_ouverture_seconde_fiche(generation: dict) -> None:
    entrees = generation["entrees"]
    episodes = generation["episodes"]
    lignes = generation["lignes"]["source.patients"]
    population = generation["population"]
    n_ipp_vers_id = _n_ipp_vers_patient_id(entrees, population)
    ligne_par_ipp = _ligne_creation_par_ipp(lignes)

    premiere_date_par_patient_id: dict[int, date] = {}
    for episode in episodes:
        pid = episode["patient_id"]
        if (
            pid not in premiere_date_par_patient_id
            or episode["date"] < premiere_date_par_patient_id[pid]
        ):
            premiere_date_par_patient_id[pid] = episode["date"]

    vt = _charger_verite_terrain(generation["execution"])
    for paire in vt["doublons"]["paires"]:
        date_creation_1 = ligne_par_ipp[paire["n_ipp_1"]]["date_attribution"]
        date_creation_2 = ligne_par_ipp[paire["n_ipp_2"]]["date_attribution"]
        patient_id_2 = n_ipp_vers_id[paire["n_ipp_2"]]
        premier_episode_2 = premiere_date_par_patient_id[patient_id_2]

        assert date_creation_2 > date_creation_1, paire
        assert date_creation_2 <= premier_episode_2, paire


def test_variations_au_moins_une_par_paire_et_repartition(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]["source.patients"]
    ligne_par_ipp = _ligne_creation_par_ipp(lignes)

    colonnes_identite = [
        "nom",
        "nom_famille_1",
        "nom_famille_2",
        "sexe",
        "date_naissance",
        "type_piece_identite",
        "n_piece_identite",
        "telephone_1",
        "adresse",
    ]

    vt = _charger_verite_terrain(generation["execution"])
    paires = vt["doublons"]["paires"]
    decompte: Counter = Counter()
    for paire in paires:
        variations = paire["variations"]
        assert len(variations) >= 1, paire
        decompte.update(variations)

        l1 = ligne_par_ipp[paire["n_ipp_1"]]
        l2 = ligne_par_ipp[paire["n_ipp_2"]]
        assert any(l1[c] != l2[c] for c in colonnes_identite), paire

    # translitteration_prenom et prenom_compose_inverse partagent la meme colonne ("nom") et
    # sont tirees comme un seul groupe (voir generator/doublons.py::_CHAMP_PAR_VARIATION) ;
    # translitteration_prenom est en outre exclue pour tout prenom absent de
    # variantes_translitteration_prenoms (mesure : la moitie des quarante prenoms de la
    # liste versionnee y figurent), ce qui reduit sa part effective et, par renormalisation,
    # augmente celle des quatre autres categories a chaque fois qu'elle est exclue. Mesure
    # sur ce jeu de donnees (graine 1) avant d'ecrire ce test : part du groupe nom observee
    # 26,2 % contre 35 % nominal (ecart -8,8 points, du a l'effet ci-dessus), les quatre
    # autres categories observees a moins de 3 points de leur poids nominal. Tolerance
    # retenue au niveau du groupe, assez large pour couvrir cet effet structurel plutot que
    # la seule variance d'echantillonnage.
    total = sum(decompte.values())
    distribution = entrees["distribution_variations"]["valeur"]
    groupes = {
        "nom": ["translitteration_prenom", "prenom_compose_inverse"],
        "date_naissance": ["faute_frappe_date_naissance"],
        "piece_identite": ["piece_identite_absente"],
        "telephone": ["telephone_different"],
        "adresse": ["adresse_mise_a_jour"],
    }
    for nom_groupe, types in groupes.items():
        part_observee = sum(decompte.get(t, 0) for t in types) / total
        part_nominale = sum(distribution[t] for t in types)
        assert abs(part_observee - part_nominale) < TOLERANCE_GROUPE_VARIATION, (
            nom_groupe,
            part_nominale,
            part_observee,
        )


def test_verite_terrain_exacte_biunivoque(generation: dict) -> None:
    entrees = generation["entrees"]
    lignes = generation["lignes"]["source.patients"]
    population = generation["population"]
    n_ipp_vers_id = _n_ipp_vers_patient_id(entrees, population)
    n_ipp_existants = {ligne["n_ipp"] for ligne in lignes}

    _, population_avant = _population_et_episodes_avant_injection(entrees, GRAINE_PARTAGEE)
    ids_avant = {p["patient_id"] for p in population_avant}

    vt = _charger_verite_terrain(generation["execution"])
    paires = vt["doublons"]["paires"]

    for paire in paires:
        assert paire["n_ipp_1"] in n_ipp_existants, paire
        assert paire["n_ipp_2"] in n_ipp_existants, paire
        assert paire["n_ipp_1"] != paire["n_ipp_2"], paire

        pid1 = n_ipp_vers_id[paire["n_ipp_1"]]
        pid2 = n_ipp_vers_id[paire["n_ipp_2"]]
        assert pid1 in ids_avant, paire
        assert pid2 not in ids_avant, paire

    n_ipp_dans_paires = {p["n_ipp_1"] for p in paires} | {p["n_ipp_2"] for p in paires}
    assert len(n_ipp_dans_paires) == 2 * len(paires)
    n_fiches_sans_doublon = n_ipp_existants - n_ipp_dans_paires
    assert len(n_fiches_sans_doublon) == len(population_avant) - len(paires)


def test_rapprochement_a_de_quoi_travailler(generation: dict) -> None:
    lignes = generation["lignes"]["source.patients"]
    ligne_par_ipp = _ligne_creation_par_ipp(lignes)

    vt = _charger_verite_terrain(generation["execution"])
    paires_verite = {(p["n_ipp_1"], p["n_ipp_2"]) for p in vt["doublons"]["paires"]}
    paires_verite |= {(b, a) for a, b in paires_verite}

    par_cle: dict[tuple, list[str]] = defaultdict(list)
    for n_ipp, ligne in ligne_par_ipp.items():
        par_cle[(ligne["nom_famille_1"], ligne["date_naissance"])].append(n_ipp)

    n_faux_appariements = 0
    for n_ipps in par_cle.values():
        if len(n_ipps) < 2:
            continue
        for i in range(len(n_ipps)):
            for j in range(i + 1, len(n_ipps)):
                if (n_ipps[i], n_ipps[j]) not in paires_verite:
                    n_faux_appariements += 1

    assert n_faux_appariements > 0


def test_reproductibilite_deux_graines(tmp_path_factory) -> None:
    entrees = {e["nom"]: e for e in config.charger_entrees()}
    racine_a1 = tmp_path_factory.mktemp("doublons_repro_a1")
    racine_a2 = tmp_path_factory.mktemp("doublons_repro_a2")
    racine_b = tmp_path_factory.mktemp("doublons_repro_b")

    execution_a1, _ = execution.executer(racine_a1, GRAINE_PARTAGEE, entrees=entrees)
    execution_a2, _ = execution.executer(racine_a2, GRAINE_PARTAGEE, entrees=entrees)
    execution_b, _ = execution.executer(racine_b, GRAINE_PARTAGEE + 1, entrees=entrees)

    vt_a1 = _charger_verite_terrain(execution_a1)
    vt_a2 = _charger_verite_terrain(execution_a2)
    vt_b = _charger_verite_terrain(execution_b)

    assert vt_a1["doublons"]["paires"] == vt_a2["doublons"]["paires"]
    # controle positif : une graine differente doit produire des paires differentes
    assert vt_a1["doublons"]["paires"] != vt_b["doublons"]["paires"]

    empreintes_a1 = {k: v for k, v in execution_a1.empreintes.items() if k.endswith(".csv")}
    empreintes_a2 = {k: v for k, v in execution_a2.empreintes.items() if k.endswith(".csv")}
    assert empreintes_a1 == empreintes_a2
