"""Génère la table des patients depuis le fil des épisodes et écrit ses lignes.

Ne construit aucun chemin, ne met en forme aucune date, ne vérifie aucun en-tête : ces
responsabilités appartiennent au module d'écriture, déjà écrit et testé. Ne tire aucun
nombre en dehors du générateur reçu en argument ; aucun générateur global, aucune
itération sur un ensemble non ordonné.
"""

from datetime import date, datetime, timedelta

import numpy as np

from generator import config, ecriture, nomenclatures, temporel

FLUX_MODIFICATION = "programme"

TABLE = "source.patients"
AGE_MAJORITE_ANNEES = 18


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _premier_episode_par_patient(episodes: list[dict]) -> dict[int, dict]:
    premiers: dict[int, dict] = {}
    for episode in episodes:
        pid = episode["patient_id"]
        if pid not in premiers:
            premiers[pid] = episode
    return premiers


def _tirage_pondere_dict(poids_par_code: dict[str, float], generateur: np.random.Generator) -> str:
    codes = list(poids_par_code.keys())
    poids = np.array([poids_par_code[c] for c in codes], dtype=float)
    poids = poids / poids.sum()
    return codes[int(generateur.choice(len(codes), p=poids))]


def _tirage_uniforme_liste(valeurs: list, generateur: np.random.Generator):
    return valeurs[int(generateur.integers(0, len(valeurs)))]


def _tirage_uniforme_nomenclature(
    nom_nomenclature: str, entrees: dict[str, dict], generateur: np.random.Generator
) -> str:
    codes = nomenclatures.codes_nomenclature(nom_nomenclature, entrees)
    return _tirage_uniforme_liste(codes, generateur)


def _tirer_tranche_age(
    categorie_premier_episode: str | None,
    entrees: dict[str, dict],
    generateur: np.random.Generator,
) -> str:
    structure = entrees["structure_age"]["valeur"]
    tranches = structure["tranches"]
    parts = np.array(structure["parts"], dtype=float)

    if categorie_premier_episode is not None:
        profils = entrees["profil_recours_demographique"]["valeur"]
        multiplicateurs = profils.get(categorie_premier_episode)
        if multiplicateurs is not None:
            parts = parts * np.array([multiplicateurs[t] for t in tranches], dtype=float)

    parts = parts / parts.sum()
    return tranches[int(generateur.choice(len(tranches), p=parts))]


def _age_en_jours_depuis_tranche(tranche: str, generateur: np.random.Generator) -> int:
    if tranche.endswith("+"):
        borne_min = int(tranche[:-1])
        borne_max = borne_min + 30
    else:
        borne_min, borne_max = (int(partie) for partie in tranche.split("-"))
    annees = int(generateur.integers(borne_min, borne_max + 1))
    jours_supplementaires = int(generateur.integers(0, 365))
    return annees * 365 + jours_supplementaires


def _bornes_jours_tranche(tranche: str) -> tuple[int, int | None]:
    if tranche.endswith("+"):
        return int(tranche[:-1]) * 365, None
    borne_min, borne_max = (int(partie) for partie in tranche.split("-"))
    return borne_min * 365, borne_max * 365 + 364


def _tranche_depuis_age_jours(age_jours: int, tranches: list[str]) -> str:
    for tranche in tranches:
        borne_min, borne_max = _bornes_jours_tranche(tranche)
        if borne_max is None:
            if age_jours >= borne_min:
                return tranche
        elif borne_min <= age_jours <= borne_max:
            return tranche
    return tranches[-1]


def _tirer_horodatage_modification(
    jour: date,
    cache_profil: dict[date, list[float]],
    entrees: dict[str, dict],
    generateur: np.random.Generator,
) -> datetime:
    # generator/calendrier.py ne reçoit pas les entrées déjà chargées et recharge la
    # configuration à chaque appel (est_ferie, est_ramadan) : un cache par jour évite de
    # relire la configuration à chaque ligne modifiée, sans réimplémenter aucune règle de
    # calendrier (temporel.profil_horaire_applicable reste l'unique source du profil).
    if jour not in cache_profil:
        cache_profil[jour] = temporel.profil_horaire_applicable(jour, FLUX_MODIFICATION, entrees)
    profil = cache_profil[jour]
    heure = int(generateur.choice(24, p=profil))
    minute = int(generateur.integers(0, 60))
    seconde = int(generateur.integers(0, 60))
    return datetime(jour.year, jour.month, jour.day, heure, minute, seconde)


def _appliquer_contraintes_egalite(ligne: dict, entrees: dict[str, dict]) -> None:
    for contrainte in entrees["contraintes_coherence"]["valeur"]:
        if contrainte["nature"] == "egalite":
            ligne[contrainte["colonne_b"]] = ligne[contrainte["colonne_a"]]


def _renseigne(colonne: str, entrees: dict[str, dict], generateur: np.random.Generator) -> bool:
    taux = entrees["taux_renseignement"]["valeur"].get(colonne)
    if taux is None:
        return True
    return bool(generateur.random() < taux)


def _tirer_foyer(
    patient_id: int,
    nb_foyers: int,
    pool: dict,
    foyers: dict[int, tuple[str, str]],
    generateur: np.random.Generator,
) -> tuple[str, str]:
    foyer_id = patient_id % nb_foyers
    if foyer_id not in foyers:
        voie = _tirage_uniforme_liste(pool["voies"], generateur)
        borne_min_voie, borne_max_voie = pool["plage_numero_voie"]
        numero_voie = int(generateur.integers(borne_min_voie, borne_max_voie + 1))
        prefixe = _tirage_uniforme_liste(pool["prefixes_telephone"], generateur)
        borne_min_tel, borne_max_tel = pool["plage_numero_telephone"]
        numero_tel = int(generateur.integers(borne_min_tel, borne_max_tel + 1))
        adresse = f"{numero_voie} {voie}"
        telephone = f"{prefixe}{numero_tel:06d}"
        foyers[foyer_id] = (adresse, telephone)
    return foyers[foyer_id]


def _generer_ligne_patient(
    patient: dict,
    premier_episode: dict | None,
    adresse: str,
    telephone_1: str,
    entrees: dict[str, dict],
    generateur: np.random.Generator,
) -> dict:
    rang = patient["patient_id"]
    date_creation_reelle = patient["date_creation"]

    categorie_premier = premier_episode["categorie"] if premier_episode else None
    date_reference_age = premier_episode["date"] if premier_episode else date_creation_reelle
    tranche = _tirer_tranche_age(categorie_premier, entrees, generateur)
    date_naissance = date_reference_age - timedelta(
        days=_age_en_jours_depuis_tranche(tranche, generateur)
    )
    if date_naissance >= date_creation_reelle:
        date_naissance = date_creation_reelle - timedelta(days=1)

    tranches = entrees["structure_age"]["valeur"]["tranches"]
    age_jours_actuel = (date_creation_reelle - date_naissance).days
    age_annees_actuel = age_jours_actuel / 365
    tranche_actuelle = _tranche_depuis_age_jours(age_jours_actuel, tranches)

    sexe = _tirage_pondere_dict(entrees["repartition_sexe"]["valeur"], generateur)

    nom_liste = entrees["prenoms_masculins" if sexe == "M" else "prenoms_feminins"]["valeur"]
    prenom = _tirage_uniforme_liste(nom_liste, generateur)

    noms_famille = entrees["noms_famille"]["valeur"]
    nom_famille_1 = _tirage_uniforme_liste(noms_famille, generateur)
    nom_famille_2 = _tirage_uniforme_liste(noms_famille, generateur)
    if not _renseigne("nom_famille_2", entrees, generateur):
        nom_famille_2 = None

    residence = entrees["repartition_residence"]["valeur"]
    region = _tirage_pondere_dict(residence["region"], generateur)
    ville_province = _tirage_pondere_dict(residence["par_region"][region], generateur)
    environnement = _tirage_pondere_dict(residence["environnement"], generateur)

    couverture = _tirage_pondere_dict(entrees["repartition_couverture"]["valeur"], generateur)

    repartition_pays = entrees["repartition_pays"]["valeur"]
    nationalite = _tirage_pondere_dict(repartition_pays, generateur)
    pays_naissance = _tirage_pondere_dict(repartition_pays, generateur)

    cle_piece = "national" if nationalite == "504" else "etranger"
    distribution_piece = entrees["distribution_piece_identite"]["valeur"][cle_piece]
    type_piece = _tirage_pondere_dict(distribution_piece, generateur)

    if age_annees_actuel < AGE_MAJORITE_ANNEES:
        etat_civil = "C"
    else:
        distribution_etat_civil = entrees["distribution_etat_civil_adulte"]["valeur"][
            tranche_actuelle
        ]
        etat_civil = _tirage_pondere_dict(distribution_etat_civil, generateur)

    cle_type_patient = "non_assure" if couverture == "SANS" else "assure"
    distribution_type_patient = entrees["distribution_type_patient"]["valeur"][cle_type_patient]
    type_patient = _tirage_pondere_dict(distribution_type_patient, generateur)

    prenom_pere = _tirage_uniforme_liste(entrees["prenoms_masculins"]["valeur"], generateur)
    prenom_mere = _tirage_uniforme_liste(entrees["prenoms_feminins"]["valeur"], generateur)

    avertissements_sms = bool(generateur.random() < entrees["taux_avertissements_sms"]["valeur"])
    avertissements_email = bool(
        generateur.random() < entrees["taux_avertissements_email"]["valeur"]
    )
    taux_exitus_tranche = entrees["taux_exitus_par_tranche"]["valeur"][tranche_actuelle]
    exitus = bool(generateur.random() < taux_exitus_tranche)

    gabarit = entrees["gabarit_identifiant_patient"]["valeur"]
    n_ipp = gabarit.format(rang=rang)

    comptes_systeme = entrees["comptes_utilisateurs_systeme"]["valeur"]
    cree_par = _tirage_uniforme_liste(comptes_systeme, generateur)

    code_postal = entrees["codes_postaux_par_ville"]["valeur"][ville_province]

    email = f"patient{rang}@exemple.ma" if _renseigne("email", entrees, generateur) else None
    telephone_2 = None
    if _renseigne("telephone_2", entrees, generateur):
        telephone_2 = f"0620{generateur.integers(0, 999999):06d}"
    telephone_3 = None
    if _renseigne("telephone_3", entrees, generateur):
        telephone_3 = f"0630{generateur.integers(0, 999999):06d}"
    telephone_4 = None
    if _renseigne("telephone_4", entrees, generateur):
        telephone_4 = f"0640{generateur.integers(0, 999999):06d}"
    commentaire = "COMMENTAIRE PATIENT" if _renseigne("commentaire", entrees, generateur) else None

    profession = None
    if _renseigne("profession", entrees, generateur):
        profession = _tirage_uniforme_liste(entrees["liste_professions"]["valeur"], generateur)

    n_piece_identite = f"{int(generateur.integers(1_000_000, 7_000_000)):09d}"
    police = f"{int(generateur.integers(1_000_000, 7_000_000)):09d}"
    n_assure = f"{int(generateur.integers(1_000_000, 7_000_000)):09d}"
    num_inscription = f"{int(generateur.integers(1_000_000, 7_000_000)):09d}"

    ligne = {
        "n_ipp": n_ipp,
        "nom": prenom,
        "nom_famille_1": nom_famille_1,
        "nom_famille_2": nom_famille_2,
        "sexe": sexe,
        "date_naissance": date_naissance,
        "type_piece_identite": type_piece,
        "n_piece_identite": n_piece_identite,
        "etat_civil": etat_civil,
        "type_patient": type_patient,
        "date_photo": date_creation_reelle,
        "modifie_par": None,
        "cree_par": cree_par,
        "date_attribution": date_creation_reelle,
        "compagnie_assurance": couverture,
        "police": police,
        "n_assure": n_assure,
        "profession": profession,
        "num_inscription": num_inscription,
        "date_inscription": date_creation_reelle,
        "type_domicile": None,
        "adresse": adresse,
        "code_postal": code_postal,
        "etat": region,
        "ville": ville_province,
        "quartier": f"QUARTIER {rang % 20}",
        "nationalite": nationalite,
        "telephone_1": telephone_1,
        "telephone_2": telephone_2,
        "telephone_3": telephone_3,
        "telephone_4": telephone_4,
        "avertissements_sms": avertissements_sms,
        "email": email,
        "avertissements_email": avertissements_email,
        "environnement": environnement,
        "nom_pere": prenom_pere,
        "nom_mere": prenom_mere,
        "etat_naissance": None,
        "ville_naissance": None,
        "pays_naissance": pays_naissance,
        "quartier_naissance": f"QUARTIER {rang % 20}",
        "commentaire": commentaire,
        "province": None,
        "exitus": exitus,
        "date_modification": None,
        "date_extraction": None,
    }
    _appliquer_contraintes_egalite(ligne, entrees)
    return ligne


def generer_lignes(
    episodes: list[dict],
    population: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> list[dict]:
    entrees = _entrees(entrees)
    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    taux_modification = entrees["taux_modification_fiche"]["valeur"]
    echelle_modification = entrees["loi_delai_modification"]["valeur"]["echelle_jours"]
    comptes_systeme = entrees["comptes_utilisateurs_systeme"]["valeur"]

    pool_foyers = entrees["pool_foyers"]["valeur"]
    nb_foyers = max(1, round(len(population) / pool_foyers["taille_moyenne_foyer"]))
    foyers: dict[int, tuple[str, str]] = {}

    premiers = _premier_episode_par_patient(episodes)
    cache_profil_horaire: dict[date, list[float]] = {}

    lignes: list[dict] = []
    for patient in sorted(population, key=lambda p: p["patient_id"]):
        premier = premiers.get(patient["patient_id"])
        adresse, telephone_1 = _tirer_foyer(
            patient["patient_id"], nb_foyers, pool_foyers, foyers, generateur
        )
        ligne_base = _generer_ligne_patient(
            patient, premier, adresse, telephone_1, entrees, generateur
        )

        date_extraction_creation = max(patient["date_creation"], date_debut)
        ligne_creation = dict(ligne_base)
        ligne_creation["date_extraction"] = date_extraction_creation
        lignes.append(ligne_creation)

        if generateur.random() < taux_modification:
            date_ancrage = premier["date"] if premier else date_extraction_creation
            date_ancrage = max(date_ancrage, date_extraction_creation)
            delai = int(generateur.exponential(echelle_modification)) + 1
            jour_modification = date_ancrage + timedelta(days=delai)
            if jour_modification <= date_fin:
                ligne_modification = dict(ligne_base)
                ligne_modification["date_modification"] = _tirer_horodatage_modification(
                    jour_modification, cache_profil_horaire, entrees, generateur
                )
                ligne_modification["modifie_par"] = _tirage_uniforme_liste(
                    comptes_systeme, generateur
                )
                ligne_modification["date_extraction"] = jour_modification
                lignes.append(ligne_modification)

    return lignes


def ecrire_patients(
    racine,
    scenario: str,
    graine: int,
    episodes: list[dict],
    population: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> ecriture.Execution:
    entrees = _entrees(entrees)
    lignes = generer_lignes(episodes, population, generateur, entrees=entrees)

    execution = ecriture.Execution(
        racine, scenario, graine, entrees["date_debut"]["valeur"], entrees["date_fin"]["valeur"]
    )
    execution.ecrire_table(TABLE, lignes)
    return execution
