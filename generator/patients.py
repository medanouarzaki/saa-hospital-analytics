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


def _tirer_adresse(pool: dict, generateur: np.random.Generator) -> str:
    voie = _tirage_uniforme_liste(pool["voies"], generateur)
    borne_min_voie, borne_max_voie = pool["plage_numero_voie"]
    numero_voie = int(generateur.integers(borne_min_voie, borne_max_voie + 1))
    return f"{numero_voie} {voie}"


def _tirer_telephone(pool: dict, generateur: np.random.Generator) -> str:
    """Un numéro STRUCTURELLEMENT IMPOSSIBLE : onze chiffres, là où le plan national en fait dix.

    Le plan de numérotation marocain donne, en forme nationale, exactement dix chiffres — le zéro
    de tête suivi de neuf chiffres significatifs. Un numéro de onze chiffres ne peut donc être
    attribué à personne, aujourd'hui ni plus tard : c'est une impossibilité de structure, et non
    une non-attribution, laquelle est administrative et révocable.

    Le septième chiffre de bourrage est le SEUL changement : le préfixe tiré et l'entier tiré
    restent les mêmes, si bien que la correspondance entre l'ancienne valeur et la nouvelle est
    injective par construction. Deux fiches dont les téléphones coïncidaient coïncident encore ;
    deux fiches qui différaient diffèrent encore. C'est ce qui protège le rapprochement, dont une
    règle de blocage compare ce champ.
    """
    prefixe = _tirage_uniforme_liste(pool["prefixes_telephone"], generateur)
    borne_min_tel, borne_max_tel = pool["plage_numero_telephone"]
    numero_tel = int(generateur.integers(borne_min_tel, borne_max_tel + 1))
    return f"{prefixe}{numero_tel:07d}"


def _tirer_foyer(
    patient_id: int,
    nb_foyers: int,
    pool: dict,
    foyers: dict[int, tuple[str, str]],
    generateur: np.random.Generator,
) -> tuple[str, str]:
    foyer_id = patient_id % nb_foyers
    if foyer_id not in foyers:
        adresse = _tirer_adresse(pool, generateur)
        telephone = _tirer_telephone(pool, generateur)
        foyers[foyer_id] = (adresse, telephone)
    return foyers[foyer_id]


# Colonnes que chaque type de changement métier est autorisé à porter (partagé avec les
# tests : la cohérence du type se vérifie contre cette même définition, pas une copie).
# `type_patient` n'est modifié qu'en conséquence d'un changement de `compagnie_assurance`
# qui ferait autrement violer la contrainte d'appartenance déclarée dans
# generator/config/coherence.yml (compagnie_assurance=SANS => type_patient != AS) ;
# il reste donc listé comme colonne autorisée de `couverture`, sans être toujours changé.
COLONNES_PAR_TYPE_MODIFICATION: dict[str, tuple[str, ...]] = {
    "demenagement": ("adresse",),
    "telephone": ("telephone_1",),
    "etat_civil": ("etat_civil",),
    "couverture": ("compagnie_assurance", "type_patient"),
}

MAX_ESSAIS_RETIRAGE = 20


def _tirer_type_modification(entrees: dict[str, dict], generateur: np.random.Generator) -> str:
    repartition = entrees["repartition_type_modification"]["valeur"]
    return _tirage_pondere_dict(repartition, generateur)


def _retirer_jusqu_a_different(tirer, valeur_actuelle, generateur: np.random.Generator):
    for _ in range(MAX_ESSAIS_RETIRAGE):
        candidat = tirer(generateur)
        if candidat != valeur_actuelle:
            return candidat
    return valeur_actuelle


def _appliquer_demenagement(ligne_base: dict, entrees: dict[str, dict], generateur) -> dict:
    pool_foyers = entrees["pool_foyers"]["valeur"]
    nouvelle_adresse = _retirer_jusqu_a_different(
        lambda g: _tirer_adresse(pool_foyers, g), ligne_base["adresse"], generateur
    )
    if nouvelle_adresse == ligne_base["adresse"]:
        return {}
    return {"adresse": nouvelle_adresse}


def _appliquer_telephone(ligne_base: dict, entrees: dict[str, dict], generateur) -> dict:
    pool_foyers = entrees["pool_foyers"]["valeur"]
    nouveau_telephone = _retirer_jusqu_a_different(
        lambda g: _tirer_telephone(pool_foyers, g), ligne_base["telephone_1"], generateur
    )
    if nouveau_telephone == ligne_base["telephone_1"]:
        return {}
    return {"telephone_1": nouveau_telephone}


def _appliquer_etat_civil(ligne_base: dict, entrees: dict[str, dict], generateur) -> dict:
    age_jours = (ligne_base["date_attribution"] - ligne_base["date_naissance"]).days
    if age_jours / 365 < AGE_MAJORITE_ANNEES:
        # domaine a une seule valeur possible ("C", codee en dur a la creation pour un
        # mineur, jamais tiree d'une distribution) : mesure au rapport, aucun changement
        # applicable pour cette fiche par ce mécanisme.
        return {}
    tranches = entrees["structure_age"]["valeur"]["tranches"]
    tranche_actuelle = _tranche_depuis_age_jours(age_jours, tranches)
    distribution = entrees["distribution_etat_civil_adulte"]["valeur"][tranche_actuelle]
    nouvel_etat_civil = _retirer_jusqu_a_different(
        lambda g: _tirage_pondere_dict(distribution, g), ligne_base["etat_civil"], generateur
    )
    if nouvel_etat_civil == ligne_base["etat_civil"]:
        return {}
    return {"etat_civil": nouvel_etat_civil}


def _appliquer_couverture(ligne_base: dict, entrees: dict[str, dict], generateur) -> dict:
    repartition_couverture = entrees["repartition_couverture"]["valeur"]
    nouvelle_compagnie = _retirer_jusqu_a_different(
        lambda g: _tirage_pondere_dict(repartition_couverture, g),
        ligne_base["compagnie_assurance"],
        generateur,
    )
    if nouvelle_compagnie == ligne_base["compagnie_assurance"]:
        return {}
    changements = {"compagnie_assurance": nouvelle_compagnie}

    # contrainte d'appartenance declaree dans generator/config/coherence.yml : une fiche
    # sans compagnie d'assurance ne peut pas rester de type Assure (AS). Recalculee ici
    # exactement comme a la creation (generator/patients.py::_generer_ligne_patient).
    if nouvelle_compagnie == "SANS" and ligne_base["type_patient"] == "AS":
        distribution_type_patient = entrees["distribution_type_patient"]["valeur"]["non_assure"]
        changements["type_patient"] = _tirage_pondere_dict(distribution_type_patient, generateur)

    return changements


_APPLICATEURS_PAR_TYPE = {
    "demenagement": _appliquer_demenagement,
    "telephone": _appliquer_telephone,
    "etat_civil": _appliquer_etat_civil,
    "couverture": _appliquer_couverture,
}


def _appliquer_changement_metier(
    ligne_base: dict, entrees: dict[str, dict], generateur: np.random.Generator
) -> tuple[str, dict]:
    """Tire un type de changement métier et l'applique sur une copie logique de
    `ligne_base`. Rend le type tiré et un mapping colonne -> nouvelle valeur, restreint
    aux colonnes réellement changées (peut être vide si le domaine de la fiche n'admet
    qu'une valeur, par exemple `etat_civil` sur un mineur — mesuré, pas masqué)."""
    type_modification = _tirer_type_modification(entrees, generateur)
    changements = _APPLICATEURS_PAR_TYPE[type_modification](ligne_base, entrees, generateur)
    return type_modification, changements


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

    domaine_email = _tirage_uniforme_liste(entrees["domaines_email"]["valeur"], generateur)
    email = (
        f"{prenom.lower()}.{nom_famille_1.lower()}@{domaine_email}"
        if _renseigne("email", entrees, generateur)
        else None
    )
    telephone_2 = None
    if _renseigne("telephone_2", entrees, generateur):
        telephone_2 = f"0620{generateur.integers(0, 999999):07d}"
    telephone_3 = None
    if _renseigne("telephone_3", entrees, generateur):
        telephone_3 = f"0630{generateur.integers(0, 999999):07d}"
    telephone_4 = None
    if _renseigne("telephone_4", entrees, generateur):
        telephone_4 = f"0640{generateur.integers(0, 999999):07d}"
    commentaire = "COMMENTAIRE PATIENT" if _renseigne("commentaire", entrees, generateur) else None

    profession = None
    if _renseigne("profession", entrees, generateur):
        profession = _tirage_uniforme_liste(entrees["liste_professions"]["valeur"], generateur)

    # La pièce d'identité reste à NEUF CHIFFRES SANS LETTRE, et c'est déjà une impossibilité de
    # structure : la carte nationale marocaine porte une ou deux lettres suivies de chiffres, si
    # bien qu'une suite purement numérique ne peut être aucune carte réelle.
    n_piece_identite = f"{int(generateur.integers(1_000_000, 7_000_000)):09d}"
    # Les trois numéros administratifs passent à DOUZE CHIFFRES. Neuf chiffres recouvraient
    # exactement l'immatriculation à la caisse nationale de sécurité sociale, qui en compte neuf ;
    # douze n'est le format d'aucun de ces registres. Le bourrage est le seul changement, l'entier
    # tiré restant le même : la correspondance reste injective.
    police = f"{int(generateur.integers(1_000_000, 7_000_000)):012d}"
    n_assure = f"{int(generateur.integers(1_000_000, 7_000_000)):012d}"
    num_inscription = f"{int(generateur.integers(1_000_000, 7_000_000)):012d}"

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
                # spawn() derive un generateur enfant sans consommer le flux du parent (a la
                # difference de .random()/.integers()/...) : les tirages du changement
                # metier restent isoles sur cette seule fiche et ne decalent pas la sequence
                # que les patients suivants de la boucle consomment depuis `generateur` --
                # mesure avant d'ecrire : sans cet isolement, le decalage se
                # propageait a toutes les fiches suivantes et faisait deriver des statistiques
                # sans rapport (occupation des lits, generator/mouvements.py) qui ne lisent
                # pourtant aucune des colonnes corrigees ici.
                generateur_metier = generateur.spawn(1)[0]
                _, changements = _appliquer_changement_metier(
                    ligne_base, entrees, generateur_metier
                )
                for colonne, valeur in changements.items():
                    ligne_modification[colonne] = valeur
                ligne_modification["date_modification"] = _tirer_horodatage_modification(
                    jour_modification, cache_profil_horaire, entrees, generateur
                )
                ligne_modification["modifie_par"] = _tirage_uniforme_liste(
                    comptes_systeme, generateur
                )
                ligne_modification["date_extraction"] = jour_modification
                lignes.append(ligne_modification)

    return lignes


def versions_par_ipp(lignes_patients: list[dict]) -> dict[str, list[dict]]:
    """Regroupe les lignes patients par `n_ipp`, une entrée par n_ipp (une ou deux versions,
    non triées ici — `version_en_vigueur` trie à l'usage). Partagé par tout lecteur aval qui
    doit choisir la version en vigueur à la date d'un événement plutôt que la dernière
    réextraite (voir `version_en_vigueur`)."""
    par_ipp: dict[str, list[dict]] = {}
    for ligne in lignes_patients:
        par_ipp.setdefault(ligne["n_ipp"], []).append(ligne)
    return par_ipp


def version_en_vigueur(versions: list[dict], jour: date) -> dict:
    """Rend la version en vigueur à `jour` : la dernière dont `date_extraction <= jour`, ou
    la première version si aucune ne satisfait cette condition (l'événement précède toute
    extraction connue — la première version est la meilleure information disponible)."""
    versions_triees = sorted(versions, key=lambda v: v["date_extraction"])
    candidates = [v for v in versions_triees if v["date_extraction"] <= jour]
    if candidates:
        return candidates[-1]
    return versions_triees[0]


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
