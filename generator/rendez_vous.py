"""Génère la table des rendez-vous depuis le fil des épisodes déjà produit.

Un épisode de consultation correspond à un rendez-vous honoré, et à un seul : le nombre
de rendez-vous honorés se déduit du nombre d'épisodes de consultation, il n'est pas tiré
indépendamment. Les absences, annulations et rendez-vous en instance sont des lignes
supplémentaires, sans épisode associé. Ne construit aucun chemin, ne met en forme aucune
date, ne vérifie aucun en-tête : ces responsabilités appartiennent au module d'écriture.
Ne tire aucun nombre en dehors du générateur reçu en argument.
"""

import bisect
import math
from datetime import date, datetime, timedelta

import numpy as np

from generator import config, ecriture, nomenclatures, temporel

TABLE = "source.rendez_vous"
FLUX = "programme"
JOURS_RECENTS_DEBORDEMENT = 30
MAX_TENTATIVES_REJET = 50


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _tirage_pondere_dict(poids_par_code: dict[str, float], generateur: np.random.Generator) -> str:
    codes = list(poids_par_code.keys())
    poids = np.array([poids_par_code[c] for c in codes], dtype=float)
    poids = poids / poids.sum()
    return codes[int(generateur.choice(len(codes), p=poids))]


def _tirage_uniforme_liste(valeurs: list, generateur: np.random.Generator):
    return valeurs[int(generateur.integers(0, len(valeurs)))]


def _renseigne(taux: float, generateur: np.random.Generator) -> bool:
    return bool(generateur.random() < taux)


class _CachesTemporelles:
    """Mémorise, par jour, le poids et le profil horaire déjà calculés par le moteur
    temporel : generator/calendrier.py ne reçoit pas les entrées déjà chargées et
    recharge la configuration à chaque appel (est_ferie, est_ramadan), ce qui rend un
    appel par ligne inutilisable sur cette table (des dizaines de milliers de lignes
    pour une poignée de centaines de jours distincts). Aucune règle de calendrier n'est
    réimplémentée ici : chaque valeur est calculée une seule fois par jour en appelant
    le moteur temporel lui-même, puis réutilisée.
    """

    def __init__(self, entrees: dict[str, dict]) -> None:
        self._entrees = entrees
        self._poids: dict[date, float] = {}
        self._profil: dict[date, list[float]] = {}

    def poids_jour(self, jour: date) -> float:
        if jour not in self._poids:
            self._poids[jour] = temporel.poids_jour(jour, FLUX, self._entrees)
        return self._poids[jour]

    def profil_horaire(self, jour: date) -> list[float]:
        if jour not in self._profil:
            self._profil[jour] = temporel.profil_horaire_applicable(jour, FLUX, self._entrees)
        return self._profil[jour]


def _jour_ouvert(jour: date, caches: _CachesTemporelles) -> bool:
    return caches.poids_jour(jour) > 0


def _jour_ouvert_le_plus_proche_apres(jour: date, caches: _CachesTemporelles) -> date:
    candidat = jour
    while not _jour_ouvert(candidat, caches):
        candidat += timedelta(days=1)
    return candidat


def _jour_ouvert_borne_inferieurement(
    jour: date, borne_min: date, caches: _CachesTemporelles
) -> date:
    # cherche le jour ouvert le plus proche sans jamais descendre sous borne_min (la date
    # de creation du patient) : une recherche arriere non bornee pourrait franchir cette
    # limite si borne_min elle-meme tombe un jour ferme.
    candidat = max(jour, borne_min)
    while candidat >= borne_min and not _jour_ouvert(candidat, caches):
        candidat -= timedelta(days=1)
    if candidat < borne_min:
        candidat = borne_min
        while not _jour_ouvert(candidat, caches):
            candidat += timedelta(days=1)
    return candidat


def _jour_ouvert_borne_superieurement(
    jour: date, borne_max: date, caches: _CachesTemporelles
) -> date:
    # symetrique de _jour_ouvert_borne_inferieurement : ne depasse jamais borne_max (la
    # fin de periode) sauf si aucun jour ouvert n'existe avant elle depuis jour, auquel
    # cas cherche en arriere depuis borne_max.
    candidat = min(jour, borne_max)
    while candidat <= borne_max and not _jour_ouvert(candidat, caches):
        candidat += timedelta(days=1)
    if candidat > borne_max:
        candidat = borne_max
        while not _jour_ouvert(candidat, caches):
            candidat -= timedelta(days=1)
    return candidat


def _tirer_horodatage(
    jour: date, caches: _CachesTemporelles, generateur: np.random.Generator
) -> datetime:
    profil = caches.profil_horaire(jour)
    heure = int(generateur.choice(24, p=profil))
    minute = int(generateur.integers(0, 60))
    seconde = int(generateur.integers(0, 60))
    return datetime(jour.year, jour.month, jour.day, heure, minute, seconde)


def _delai_lognormal(
    mediane_jours: float, ecart_type_log: float, generateur: np.random.Generator
) -> int:
    delai = generateur.lognormal(math.log(mediane_jours), ecart_type_log)
    return max(0, int(round(delai)))


def _delai_biaise_longue_attente(
    mediane_jours: float,
    ecart_type_log: float,
    pente: float,
    generateur: np.random.Generator,
) -> int:
    plage_max = mediane_jours * 6
    poids_max = 1 + pente * plage_max
    delai = 0
    for _ in range(MAX_TENTATIVES_REJET):
        delai = _delai_lognormal(mediane_jours, ecart_type_log, generateur)
        poids = 1 + pente * min(delai, plage_max)
        if generateur.random() < poids / poids_max:
            return delai
    return delai


def _patient_existant_a(
    jour: date,
    population_triee: list[dict],
    dates_creation: list[date],
    generateur: np.random.Generator,
) -> dict:
    limite = bisect.bisect_right(dates_creation, jour)
    if limite == 0:
        return population_triee[0]
    indice = int(generateur.integers(0, limite))
    return population_triee[indice]


def _construire_adressage(
    origine: str, entrees: dict[str, dict], generateur: np.random.Generator
) -> tuple[str | None, str | None, str | None]:
    contrainte = next(
        c
        for c in entrees["contraintes_coherence_rendez_vous"]["valeur"]
        if c["colonne_b"] == "hopital_cs"
    )
    if origine != contrainte["valeur_a_declenchante"]:
        return None, None, None

    hopital_cs = _tirage_uniforme_liste(
        nomenclatures.codes_nomenclature("nomenclature_etablissements_partenaires", entrees),
        generateur,
    )
    medecin_ext = None
    if _renseigne(entrees["taux_medecin_adresse"]["valeur"], generateur):
        noms_famille = entrees["noms_famille"]["valeur"]
        medecin_ext = f"Dr. {_tirage_uniforme_liste(noms_famille, generateur)}"
    service_ext = None
    if _renseigne(entrees["taux_service_adresse"]["valeur"], generateur):
        service_ext = _tirage_uniforme_liste(
            entrees["liste_services_adressants"]["valeur"], generateur
        )
    return hopital_cs, medecin_ext, service_ext


def _construire_ligne_base(
    n_ipp: str,
    activite: str,
    agenda: str,
    type_attention: str,
    comptes: list[str],
    entrees: dict[str, dict],
    generateur: np.random.Generator,
) -> dict:
    return {
        "n_rdv": None,
        "n_ipp": n_ipp,
        "agenda": agenda,
        "activite": activite,
        "origine": None,
        "hopital_cs": None,
        "medecin_ext": None,
        "service_ext": None,
        "observations": None,
        "date_rendez_vous": None,
        "rdv_supplementaire": None,
        "type_attention": type_attention,
        "etat": None,
        "duree": int(entrees["duree_minutes"]["valeur"]),
        "date_reception": None,
        "imprimer_donnees": False,
        "cree_par": _tirage_uniforme_liste(comptes, generateur),
        "date_creation": None,
        "modifie_par": None,
        "date_mod": None,
        "confirme_par": None,
        "date_conf": None,
        "annule_par": None,
        "date_annul": None,
        "liste_attente_service": None,
        "liste_attente_agenda": None,
        "liste_attente_activite": None,
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
    caches = _CachesTemporelles(entrees)

    correspondance_activite_agenda = entrees["correspondance_activite_agenda"]["valeur"]
    repartition_activites = entrees["repartition_activites_rdv"]["valeur"]
    repartition_types_attention = entrees["repartition_types_attention"]["valeur"]
    delais_medians = entrees["delai_rdv_par_specialite"]["valeur"]
    ecart_type_log = entrees["ecart_type_log_delai"]["valeur"]
    pente = entrees["pente_absenteisme_delai"]["valeur"]
    taux_absenteisme = entrees["taux_absenteisme_par_specialite"]["valeur"]
    taux_annulation = entrees["taux_annulation"]["valeur"]
    part_jour_meme = entrees["part_rdv_jour_meme"]["valeur"]
    part_adresses = entrees["part_patients_adresses"]["valeur"]
    part_liste_attente = entrees["part_liste_attente"]["valeur"]
    comptes = entrees["comptes_utilisateurs_rdv"]["valeur"]
    gabarit_ipp = entrees["gabarit_identifiant_patient"]["valeur"]
    code_origine_adresse = "AU"
    code_etat_absence = entrees["code_etat_absence"]["valeur"]
    taux_renseignement_modif = entrees["taux_renseignement_rdv"]["valeur"]["modifie_par"]

    for activite in repartition_activites:
        if activite not in delais_medians:
            raise KeyError(
                f"activite sans delai declare dans delai_rdv_par_specialite : {activite}"
            )
        if activite not in taux_absenteisme:
            raise KeyError(
                f"activite sans taux declare dans taux_absenteisme_par_specialite : {activite}"
            )

    population_triee = sorted(population, key=lambda p: p["date_creation"])
    dates_creation = [p["date_creation"] for p in population_triee]
    population_par_id = {p["patient_id"]: p for p in population}

    episodes_consultation = [e for e in episodes if e["categorie"] == "C"]

    premiers_par_patient: dict[int, dict] = {}
    for episode in episodes:
        pid = episode["patient_id"]
        if pid not in premiers_par_patient:
            premiers_par_patient[pid] = episode

    episodes_par_activite: dict[str, list[dict]] = {a: [] for a in repartition_activites}
    for episode in episodes_consultation:
        patient = population_par_id[episode["patient_id"]]
        active_precomputee = (
            premiers_par_patient.get(episode["patient_id"]) is episode
            and patient.get("activite_creation") is not None
        )
        if active_precomputee:
            activite = patient["activite_creation"]
        else:
            activite = _tirage_pondere_dict(repartition_activites, generateur)
        episodes_par_activite[activite].append(episode)

    lignes: list[dict] = []
    rang_rdv = 0

    def prochain_n_rdv() -> str:
        nonlocal rang_rdv
        rang_rdv += 1
        return f"RDV-{rang_rdv:07d}"

    def n_ipp_pour(patient_id: int) -> str:
        return gabarit_ipp.format(rang=patient_id)

    def choisir_type_attention() -> str:
        return _tirage_pondere_dict(repartition_types_attention, generateur)

    def tirer_prise(rendez_vous_date: date, delai: int, date_min: date) -> date:
        prise = rendez_vous_date - timedelta(days=delai)
        return _jour_ouvert_borne_inferieurement(prise, date_min, caches)

    def construire_modification(jour_reference: date) -> tuple[str | None, datetime | None]:
        if not _renseigne(taux_renseignement_modif, generateur):
            return None, None
        modifie_par = _tirage_uniforme_liste(comptes, generateur)
        date_mod = _tirer_horodatage(jour_reference, caches, generateur)
        return modifie_par, date_mod

    for activite, episodes_activite in episodes_par_activite.items():
        agenda = correspondance_activite_agenda[activite]
        mediane = delais_medians[activite]
        p_abs = taux_absenteisme[activite]

        # --- rendez-vous honores : un par episode, tenu ---
        for episode in episodes_activite:
            jour_rdv = episode["date"]
            patient_id = episode["patient_id"]
            n_ipp = n_ipp_pour(patient_id)
            patient = population_par_id[patient_id]
            date_creation_patient = patient["date_creation"]

            est_premier = premiers_par_patient.get(patient_id) is episode
            if est_premier and patient.get("activite_creation") == activite:
                # la date de prise a deja ete fixee par generator/parcours.py au moment
                # ou la fiche a ete ouverte : ne pas la retirer independamment ici, sous
                # peine de contredire cette decision deja prise et deja coherente.
                jour_prise = date_creation_patient
            else:
                marge_disponible = (jour_rdv - date_creation_patient).days
                if marge_disponible <= 0 or generateur.random() < part_jour_meme:
                    delai = 0
                else:
                    delai = _delai_lognormal(mediane, ecart_type_log, generateur)
                    delai = min(delai, marge_disponible)
                jour_prise = tirer_prise(jour_rdv, delai, date_creation_patient)

            ligne = _construire_ligne_base(
                n_ipp, activite, agenda, choisir_type_attention(), comptes, entrees, generateur
            )
            ligne["n_rdv"] = prochain_n_rdv()
            ligne["etat"] = "HO"
            ligne["rdv_supplementaire"] = False
            ligne["date_rendez_vous"] = _tirer_horodatage(jour_rdv, caches, generateur)
            ligne["date_creation"] = _tirer_horodatage(jour_prise, caches, generateur)
            ligne["date_reception"] = ligne["date_creation"]
            ligne["confirme_par"] = _tirage_uniforme_liste(comptes, generateur)
            ligne["date_conf"] = _tirer_horodatage(jour_prise, caches, generateur)
            ligne["origine"] = code_origine_adresse if generateur.random() < part_adresses else "SP"
            ligne["hopital_cs"], ligne["medecin_ext"], ligne["service_ext"] = _construire_adressage(
                ligne["origine"], entrees, generateur
            )
            ligne["modifie_par"], ligne["date_mod"] = construire_modification(jour_rdv)
            ligne["date_extraction"] = max(jour_prise, date_debut)
            lignes.append(ligne)

        # --- volume total deduit des taux, absences et annulations en lignes supplementaires ---
        honores = len(episodes_activite)
        if honores == 0:
            continue
        denominateur = 1 - p_abs - taux_annulation
        total_active = honores / denominateur if denominateur > 0 else honores
        n_absences = round(total_active * p_abs)
        n_annulations = round(total_active * taux_annulation)

        jours_ouverts_periode = [
            date_debut + timedelta(days=d)
            for d in range((date_fin - date_debut).days + 1)
            if _jour_ouvert(date_debut + timedelta(days=d), caches)
        ]

        for _ in range(n_absences):
            jour_prise = _tirage_uniforme_liste(jours_ouverts_periode, generateur)
            patient = _patient_existant_a(jour_prise, population_triee, dates_creation, generateur)
            n_ipp = n_ipp_pour(patient["patient_id"])
            jour_prise = _jour_ouvert_borne_inferieurement(
                jour_prise, patient["date_creation"], caches
            )

            delai = _delai_biaise_longue_attente(mediane, ecart_type_log, pente, generateur)
            jour_rdv = jour_prise + timedelta(days=delai)
            jour_rdv = _jour_ouvert_borne_superieurement(jour_rdv, date_fin, caches)

            ligne = _construire_ligne_base(
                n_ipp, activite, agenda, choisir_type_attention(), comptes, entrees, generateur
            )
            ligne["n_rdv"] = prochain_n_rdv()
            ligne["etat"] = code_etat_absence
            ligne["rdv_supplementaire"] = True
            ligne["date_rendez_vous"] = _tirer_horodatage(jour_rdv, caches, generateur)
            ligne["date_creation"] = _tirer_horodatage(jour_prise, caches, generateur)
            ligne["date_reception"] = ligne["date_creation"]
            ligne["confirme_par"] = _tirage_uniforme_liste(comptes, generateur)
            ligne["date_conf"] = _tirer_horodatage(jour_prise, caches, generateur)
            ligne["origine"] = code_origine_adresse if generateur.random() < part_adresses else "SP"
            ligne["hopital_cs"], ligne["medecin_ext"], ligne["service_ext"] = _construire_adressage(
                ligne["origine"], entrees, generateur
            )
            ligne["modifie_par"], ligne["date_mod"] = construire_modification(jour_prise)
            ligne["date_extraction"] = max(jour_prise, date_debut)
            lignes.append(ligne)

        for _ in range(n_annulations):
            jour_prise = _tirage_uniforme_liste(jours_ouverts_periode, generateur)
            patient = _patient_existant_a(jour_prise, population_triee, dates_creation, generateur)
            n_ipp = n_ipp_pour(patient["patient_id"])
            jour_prise = _jour_ouvert_borne_inferieurement(
                jour_prise, patient["date_creation"], caches
            )

            delai = _delai_lognormal(mediane, ecart_type_log, generateur)
            jour_rdv = jour_prise + timedelta(days=delai)
            jour_rdv = _jour_ouvert_borne_superieurement(jour_rdv, date_fin, caches)

            ligne = _construire_ligne_base(
                n_ipp, activite, agenda, choisir_type_attention(), comptes, entrees, generateur
            )
            ligne["n_rdv"] = prochain_n_rdv()
            ligne["etat"] = "AN"
            ligne["rdv_supplementaire"] = True
            ligne["date_rendez_vous"] = _tirer_horodatage(jour_rdv, caches, generateur)
            ligne["date_creation"] = _tirer_horodatage(jour_prise, caches, generateur)
            ligne["date_reception"] = ligne["date_creation"]
            ligne["annule_par"] = _tirage_uniforme_liste(comptes, generateur)
            jour_annulation = _jour_ouvert_borne_inferieurement(jour_rdv, jour_prise, caches)
            ligne["date_annul"] = _tirer_horodatage(jour_annulation, caches, generateur)
            ligne["origine"] = code_origine_adresse if generateur.random() < part_adresses else "SP"
            ligne["hopital_cs"], ligne["medecin_ext"], ligne["service_ext"] = _construire_adressage(
                ligne["origine"], entrees, generateur
            )
            ligne["modifie_par"], ligne["date_mod"] = construire_modification(jour_prise)
            ligne["date_extraction"] = max(jour_prise, date_debut)
            lignes.append(ligne)

        # --- debordement de periode : prises recentes dont le rendez-vous depasse la fin ---
        n_debordement = max(1, round(honores * 0.03))
        bornes_recentes = [
            date_fin - timedelta(days=d)
            for d in range(JOURS_RECENTS_DEBORDEMENT)
            if _jour_ouvert(date_fin - timedelta(days=d), caches)
        ]
        if not bornes_recentes:
            bornes_recentes = [date_fin]

        for _ in range(n_debordement):
            jour_prise = _tirage_uniforme_liste(bornes_recentes, generateur)
            patient = _patient_existant_a(jour_prise, population_triee, dates_creation, generateur)
            n_ipp = n_ipp_pour(patient["patient_id"])
            jour_prise = _jour_ouvert_borne_inferieurement(
                jour_prise, patient["date_creation"], caches
            )

            delai = _delai_lognormal(mediane, ecart_type_log, generateur)
            jour_rdv = jour_prise + timedelta(days=max(delai, (date_fin - jour_prise).days + 1))
            jour_rdv = _jour_ouvert_le_plus_proche_apres(jour_rdv, caches)

            ligne = _construire_ligne_base(
                n_ipp, activite, agenda, choisir_type_attention(), comptes, entrees, generateur
            )
            ligne["n_rdv"] = prochain_n_rdv()
            ligne["etat"] = "EI"
            ligne["rdv_supplementaire"] = True
            ligne["date_rendez_vous"] = _tirer_horodatage(jour_rdv, caches, generateur)
            ligne["date_creation"] = _tirer_horodatage(jour_prise, caches, generateur)
            ligne["date_reception"] = ligne["date_creation"]
            if generateur.random() < part_liste_attente:
                ligne["liste_attente_service"] = "CE"
                ligne["liste_attente_agenda"] = agenda
                ligne["liste_attente_activite"] = activite
            ligne["origine"] = code_origine_adresse if generateur.random() < part_adresses else "SP"
            ligne["hopital_cs"], ligne["medecin_ext"], ligne["service_ext"] = _construire_adressage(
                ligne["origine"], entrees, generateur
            )
            ligne["modifie_par"], ligne["date_mod"] = construire_modification(jour_prise)
            ligne["date_extraction"] = max(jour_prise, date_debut)
            lignes.append(ligne)

    return lignes


def ecrire_rendez_vous(
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
