"""Génère la table des patients depuis le fil des épisodes et écrit ses lignes.

Ne construit aucun chemin, ne met en forme aucune date, ne vérifie aucun en-tête : ces
responsabilités appartiennent au module d'écriture, déjà écrit et testé. Ne tire aucun
nombre en dehors du générateur reçu en argument ; aucun générateur global, aucune
itération sur un ensemble non ordonné.
"""

from datetime import date, timedelta

import numpy as np

from generator import config, ecriture, nomenclatures

TABLE = "source.patients"


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


def _generer_ligne_patient(
    patient: dict,
    premier_episode: dict | None,
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

    sexe = _tirage_pondere_dict(entrees["repartition_sexe"]["valeur"], generateur)

    nom_liste = entrees["prenoms_masculins" if sexe == "M" else "prenoms_feminins"]["valeur"]
    prenom = _tirage_uniforme_liste(nom_liste, generateur)

    noms_famille = entrees["noms_famille"]["valeur"]
    nom_famille_1 = _tirage_uniforme_liste(noms_famille, generateur)
    nom_famille_2 = _tirage_uniforme_liste(noms_famille, generateur)

    residence = entrees["repartition_residence"]["valeur"]
    region = _tirage_pondere_dict(residence["region"], generateur)
    province = _tirage_pondere_dict(residence["province"], generateur)
    ville = _tirage_pondere_dict(residence["ville"], generateur)
    environnement = _tirage_pondere_dict(residence["environnement"], generateur)

    couverture = _tirage_pondere_dict(entrees["repartition_couverture"]["valeur"], generateur)

    repartition_pays = entrees["repartition_pays"]["valeur"]
    nationalite = _tirage_pondere_dict(repartition_pays, generateur)
    pays_naissance = _tirage_pondere_dict(repartition_pays, generateur)

    type_piece = _tirage_uniforme_nomenclature(
        "nomenclature_type_piece_identite", entrees, generateur
    )
    etat_civil = _tirage_uniforme_nomenclature("nomenclature_etat_civil", entrees, generateur)
    type_patient = _tirage_uniforme_nomenclature("nomenclature_type_patient", entrees, generateur)
    type_domicile = _tirage_uniforme_nomenclature("nomenclature_type_domicile", entrees, generateur)

    prenom_pere = _tirage_uniforme_liste(entrees["prenoms_masculins"]["valeur"], generateur)
    prenom_mere = _tirage_uniforme_liste(entrees["prenoms_feminins"]["valeur"], generateur)

    avertissements_sms = bool(generateur.random() < entrees["taux_avertissements_sms"]["valeur"])
    avertissements_email = bool(
        generateur.random() < entrees["taux_avertissements_email"]["valeur"]
    )
    exitus = bool(generateur.random() < entrees["taux_exitus"]["valeur"])

    gabarit = entrees["gabarit_identifiant_patient"]["valeur"]
    n_ipp = gabarit.format(rang=rang)

    return {
        "n_ipp": n_ipp,
        "nom": prenom,
        "nom_famille_1": nom_famille_1,
        "nom_famille_2": nom_famille_2,
        "sexe": sexe,
        "date_naissance": date_naissance,
        "type_piece_identite": type_piece,
        "n_piece_identite": f"PIECE{rang:08d}",
        "etat_civil": etat_civil,
        "type_patient": type_patient,
        "date_photo": date_creation_reelle,
        "modifie_par": None,
        "cree_par": "SYSTEME",
        "date_attribution": date_creation_reelle,
        "compagnie_assurance": couverture,
        "police": f"POL{rang:08d}",
        "n_assure": f"ASS{rang:08d}",
        "profession": "NON PRECISEE",
        "num_inscription": f"INS{rang:08d}",
        "date_inscription": date_creation_reelle,
        "type_domicile": type_domicile,
        "adresse": f"ADRESSE {rang}",
        "code_postal": "50000",
        "etat": region,
        "ville": ville,
        "quartier": f"QUARTIER {rang % 20}",
        "nationalite": nationalite,
        "telephone_1": f"06{rang:08d}",
        "telephone_2": "",
        "telephone_3": "",
        "telephone_4": "",
        "avertissements_sms": avertissements_sms,
        "email": f"patient{rang}@exemple.ma",
        "avertissements_email": avertissements_email,
        "environnement": environnement,
        "nom_pere": prenom_pere,
        "nom_mere": prenom_mere,
        "etat_naissance": region,
        "ville_naissance": ville,
        "pays_naissance": pays_naissance,
        "quartier_naissance": f"QUARTIER {rang % 20}",
        "commentaire": "",
        "province": province,
        "exitus": exitus,
        "date_modification": None,
        "date_extraction": None,
    }


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

    premiers = _premier_episode_par_patient(episodes)

    lignes: list[dict] = []
    for patient in sorted(population, key=lambda p: p["patient_id"]):
        premier = premiers.get(patient["patient_id"])
        ligne_base = _generer_ligne_patient(patient, premier, entrees, generateur)

        date_extraction_creation = max(patient["date_creation"], date_debut)
        ligne_creation = dict(ligne_base)
        ligne_creation["date_extraction"] = date_extraction_creation
        lignes.append(ligne_creation)

        if generateur.random() < taux_modification:
            date_ancrage = premier["date"] if premier else date_extraction_creation
            date_ancrage = max(date_ancrage, date_extraction_creation)
            delai = int(generateur.exponential(echelle_modification)) + 1
            date_modification = date_ancrage + timedelta(days=delai)
            if date_modification <= date_fin:
                ligne_modification = dict(ligne_base)
                ligne_modification["date_modification"] = date_modification
                ligne_modification["modifie_par"] = "SYSTEME"
                ligne_modification["date_extraction"] = date_modification
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
