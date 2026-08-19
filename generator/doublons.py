"""Injecte des doublons d'identité dans une population déjà construite.

Appelé après `generator.patients.generer_lignes` (les fiches d'origine doivent déjà
exister pour que les fiches en double en soient des copies variées, pas des identités
indépendantes) et avant tout module qui consulte `episodes`/`population` pour une table
postérieure à `source.patients` dans le registre de `generator/execution.py`. Mute
`episodes` et `population` en place : les épisodes postérieurs au point de scission d'une
personne retenue changent de `patient_id`, et une entrée de population est ajoutée par
personne retenue. N'invente, ne supprime ni ne déplace dans le temps aucun épisode ; ne
change le nombre de personnes d'aucune façon, seulement le nombre de fiches qui les
portent.

Le nombre de personnes recevant une seconde fiche est calculé depuis le taux configuré et
l'effectif, puis exactement ce nombre est choisi au hasard parmi les personnes éligibles
(allocation exacte, pas un tirage indépendant par personne) — même principe que
`generator/mouvements.py::generer_lignes` pour le mode d'admission urgence.
"""

from collections import defaultdict
from datetime import date, timedelta

import numpy as np

from generator import config

VARIATIONS_CONNUES = (
    "translitteration_prenom",
    "prenom_compose_inverse",
    "faute_frappe_date_naissance",
    "piece_identite_absente",
    "telephone_different",
    "adresse_mise_a_jour",
)


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _tirage_uniforme_liste(valeurs: list, generateur: np.random.Generator):
    return valeurs[int(generateur.integers(0, len(valeurs)))]


def _episodes_par_patient_tries(episodes: list[dict]) -> dict[int, list[int]]:
    par_patient: dict[int, list[int]] = defaultdict(list)
    for indice, episode in enumerate(episodes):
        par_patient[episode["patient_id"]].append(indice)
    for patient_id in par_patient:
        par_patient[patient_id].sort(key=lambda i: episodes[i]["date"])
    return par_patient


def personnes_eligibles(episodes: list[dict], population: list[dict]) -> list[int]:
    del population
    par_patient = _episodes_par_patient_tries(episodes)
    eligibles = []
    for patient_id, indices in par_patient.items():
        premiere_date = episodes[indices[0]]["date"]
        derniere_date = episodes[indices[-1]]["date"]
        if len(indices) >= 2 and derniere_date > premiere_date:
            eligibles.append(patient_id)
    return sorted(eligibles)


def _types_eligibles_pour_prenom(prenom: str, entrees: dict[str, dict]) -> list[str]:
    variantes = entrees["variantes_translitteration_prenoms"]["valeur"]
    types = list(entrees["distribution_variations"]["valeur"].keys())
    if prenom not in variantes:
        types = [t for t in types if t != "translitteration_prenom"]
    return types


# translitteration_prenom et prenom_compose_inverse portent toutes deux sur la colonne
# "nom" : les combiner sur une meme paire n'aurait pas de sens (laquelle l'emporterait ?).
# Regroupees sous une seule cle de champ pour que la selection choisisse au plus une
# variation par champ touche, jamais deux qui se contrediraient sur la meme colonne.
_CHAMP_PAR_VARIATION = {
    "translitteration_prenom": "nom",
    "prenom_compose_inverse": "nom",
    "faute_frappe_date_naissance": "date_naissance",
    "piece_identite_absente": "piece_identite",
    "telephone_different": "telephone",
    "adresse_mise_a_jour": "adresse",
}


def _choisir_variations(
    types_eligibles: list[str],
    n_variations: int,
    distribution: dict[str, float],
    generateur: np.random.Generator,
) -> list[str]:
    groupes: dict[str, list[str]] = defaultdict(list)
    for type_variation in types_eligibles:
        groupes[_CHAMP_PAR_VARIATION[type_variation]].append(type_variation)
    champs = sorted(groupes.keys())

    n_variations = min(n_variations, len(champs))
    poids_champs = np.array([sum(distribution[t] for t in groupes[c]) for c in champs], dtype=float)
    poids_champs = poids_champs / poids_champs.sum()
    indices_champs = generateur.choice(
        len(champs), size=n_variations, replace=False, p=poids_champs
    )

    choisies = []
    for indice in indices_champs:
        membres = groupes[champs[indice]]
        if len(membres) == 1:
            choisies.append(membres[0])
        else:
            poids_membres = np.array([distribution[t] for t in membres], dtype=float)
            poids_membres = poids_membres / poids_membres.sum()
            choisies.append(membres[int(generateur.choice(len(membres), p=poids_membres))])
    return sorted(choisies)


def _appliquer_translitteration_prenom(
    ligne: dict, ligne_source: dict, entrees: dict[str, dict], generateur: np.random.Generator
) -> None:
    prenom_origine = ligne_source["nom"]
    variantes = [
        v
        for v in entrees["variantes_translitteration_prenoms"]["valeur"][prenom_origine]
        if v != prenom_origine
    ]
    ligne["nom"] = _tirage_uniforme_liste(variantes, generateur)


def _appliquer_prenom_compose_inverse(
    ligne: dict,
    lignes_source_meme_ipp: list[dict],
    entrees: dict[str, dict],
    generateur: np.random.Generator,
) -> None:
    paires = entrees["paires_prenoms_composes"]["valeur"]
    partie_a, partie_b = _tirage_uniforme_liste(paires, generateur)
    for ligne_originale in lignes_source_meme_ipp:
        ligne_originale["nom"] = f"{partie_a} {partie_b}"
    ligne["nom"] = f"{partie_b} {partie_a}"


def _appliquer_faute_frappe_date_naissance(
    ligne: dict, date_limite: date, generateur: np.random.Generator
) -> None:
    origine = ligne["date_naissance"]
    delta_jours = int(generateur.integers(1, 31))
    signe = 1 if int(generateur.integers(0, 2)) == 0 else -1
    candidate = origine + timedelta(days=signe * delta_jours)
    if candidate >= date_limite:
        candidate = origine - timedelta(days=delta_jours)
    ligne["date_naissance"] = candidate


def _appliquer_piece_identite_absente(ligne: dict) -> None:
    ligne["type_piece_identite"] = None
    ligne["n_piece_identite"] = None


def _appliquer_telephone_different(ligne: dict, generateur: np.random.Generator) -> None:
    origine = ligne["telephone_1"]
    candidat = origine
    while candidat == origine:
        # Onze chiffres, comme tout téléphone produit par ce générateur : la fiche en double
        # ne doit pas être le seul endroit où un numéro reprenne une forme possible.
        candidat = f"0620{int(generateur.integers(0, 999999)):07d}"
    ligne["telephone_1"] = candidat


def _appliquer_adresse_mise_a_jour(
    ligne: dict, entrees: dict[str, dict], generateur: np.random.Generator
) -> None:
    pool = entrees["pool_foyers"]["valeur"]
    origine = ligne["adresse"]
    candidat = origine
    while candidat == origine:
        voie = _tirage_uniforme_liste(pool["voies"], generateur)
        borne_min, borne_max = pool["plage_numero_voie"]
        numero = int(generateur.integers(borne_min, borne_max + 1))
        candidat = f"{numero} {voie}"
    ligne["adresse"] = candidat


_APPLICATEURS = {
    "translitteration_prenom": lambda ligne, source, source_meme_ipp, entrees, generateur: (
        _appliquer_translitteration_prenom(ligne, source, entrees, generateur)
    ),
    "prenom_compose_inverse": lambda ligne, source, source_meme_ipp, entrees, generateur: (
        _appliquer_prenom_compose_inverse(ligne, source_meme_ipp, entrees, generateur)
    ),
    "faute_frappe_date_naissance": lambda ligne, source, source_meme_ipp, entrees, generateur: (
        _appliquer_faute_frappe_date_naissance(ligne, ligne["date_attribution"], generateur)
    ),
    "piece_identite_absente": lambda ligne, source, source_meme_ipp, entrees, generateur: (
        _appliquer_piece_identite_absente(ligne)
    ),
    "telephone_different": lambda ligne, source, source_meme_ipp, entrees, generateur: (
        _appliquer_telephone_different(ligne, generateur)
    ),
    "adresse_mise_a_jour": lambda ligne, source, source_meme_ipp, entrees, generateur: (
        _appliquer_adresse_mise_a_jour(ligne, entrees, generateur)
    ),
}


def injecter_doublons(
    episodes: list[dict],
    population: list[dict],
    lignes_patients: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    entrees = _entrees(entrees)
    taux = entrees["taux_doublons"]["valeur"]
    bornes_n_variations = entrees["nombre_variations_par_paire"]["valeur"]
    distribution = entrees["distribution_variations"]["valeur"]
    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    gabarit_ipp = entrees["gabarit_identifiant_patient"]["valeur"]

    par_patient = _episodes_par_patient_tries(episodes)
    eligibles = personnes_eligibles(episodes, population)

    n_personnes = len(population)
    n_cible = round(taux * n_personnes)
    if n_cible > len(eligibles):
        raise ValueError(
            "effectif de personnes eligibles insuffisant pour le taux de doublons "
            f"configure ({len(eligibles)} eligibles, {n_cible} requis)"
        )

    if n_cible > 0:
        indices_choisis = generateur.choice(len(eligibles), size=n_cible, replace=False)
        patients_retenus = sorted(int(eligibles[i]) for i in indices_choisis)
    else:
        patients_retenus = []

    lignes_par_ipp: dict[str, list[dict]] = defaultdict(list)
    for ligne in lignes_patients:
        lignes_par_ipp[ligne["n_ipp"]].append(ligne)

    lignes_doublons: list[dict] = []
    paires: list[dict] = []

    for patient_id in patients_retenus:
        indices_tries = par_patient[patient_id]
        dates_episodes = [episodes[i]["date"] for i in indices_tries]
        premiere_date = dates_episodes[0]
        # loi_ouverture_seconde_fiche == "uniforme" : tirage uniforme parmi les points de
        # scission eligibles (indices dont l'episode est strictement posterieur au premier).
        candidats_k = [k for k in range(1, len(indices_tries)) if dates_episodes[k] > premiere_date]
        k = candidats_k[int(generateur.integers(0, len(candidats_k)))]
        date_seconde = dates_episodes[k]

        nouveau_id = len(population)
        population.append(
            {"patient_id": nouveau_id, "date_creation": date_seconde, "activite_creation": None}
        )
        for indice_episode in indices_tries[k:]:
            episodes[indice_episode]["patient_id"] = nouveau_id

        n_ipp_source = gabarit_ipp.format(rang=patient_id)
        n_ipp_nouveau = gabarit_ipp.format(rang=nouveau_id)
        lignes_source_meme_ipp = lignes_par_ipp[n_ipp_source]
        ligne_source = next(
            ligne for ligne in lignes_source_meme_ipp if ligne["date_modification"] is None
        )

        n_variations = int(
            generateur.integers(bornes_n_variations["min"], bornes_n_variations["max"] + 1)
        )
        types_eligibles = _types_eligibles_pour_prenom(ligne_source["nom"], entrees)
        variations_choisies = _choisir_variations(
            types_eligibles, n_variations, distribution, generateur
        )

        ligne = dict(ligne_source)
        ligne["n_ipp"] = n_ipp_nouveau
        ligne["date_photo"] = date_seconde
        ligne["date_attribution"] = date_seconde
        ligne["date_inscription"] = date_seconde
        ligne["date_extraction"] = max(date_seconde, date_debut)
        ligne["date_modification"] = None
        ligne["modifie_par"] = None
        ligne["cree_par"] = _tirage_uniforme_liste(
            entrees["comptes_utilisateurs_systeme"]["valeur"], generateur
        )

        for type_variation in variations_choisies:
            _APPLICATEURS[type_variation](
                ligne, ligne_source, lignes_source_meme_ipp, entrees, generateur
            )

        lignes_doublons.append(ligne)
        paires.append(
            {
                "patient_id_1": patient_id,
                "patient_id_2": nouveau_id,
                "n_ipp_1": n_ipp_source,
                "n_ipp_2": n_ipp_nouveau,
                "date_creation_1": ligne_source["date_attribution"],
                "date_creation_2": date_seconde,
                "variations": variations_choisies,
            }
        )

    return lignes_doublons, paires
