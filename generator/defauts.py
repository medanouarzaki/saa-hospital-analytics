"""Injecte les défauts de surface restants du cadrage, en une passe distincte après que
toutes les tables bien formées existent (voir `generator/execution.py::executer`, appelée
après la boucle de génération, avant l'écriture des fichiers).

C'est cette séparation qui permet de compter exactement ce qui a été altéré : chaque
catégorie sélectionne un nombre exact de cibles (allocation exacte, jamais un tirage
indépendant — même principe que `generator/doublons.py`) parmi les lignes éligibles, mute
en place, et enregistre chaque altération (catégorie, table, colonne, identifiant, valeur
avant, valeur après). Ne touche aucune colonne codée (conformité aux nomenclatures) ni
aucune colonne identifiante (intégrité référentielle) : les six catégories ci-dessous
portent explicitement sur des colonnes de texte libre ou de date/horodatage non
identifiantes.
"""

from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

from generator import config

TABLE_PATIENTS = "source.patients"
TABLE_RDV = "source.rendez_vous"
TABLE_FACTURES = "source.factures"
TABLE_PEC = "source.prises_en_charge"

_ACCENTS = str.maketrans("éèêëàâäîïôöùûüç", "eeeeaaaiioouuuc")


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _selectionner(indices_eligibles: list, n_cible: int, generateur: np.random.Generator) -> list:
    n_cible = min(n_cible, len(indices_eligibles))
    if n_cible <= 0:
        return []
    tirage = generateur.choice(len(indices_eligibles), size=n_cible, replace=False)
    return sorted(indices_eligibles[int(i)] for i in tirage)


def _regrouper_par_ipp(lignes: list[dict]) -> dict[str, list[dict]]:
    par_ipp: dict[str, list[dict]] = defaultdict(list)
    for ligne in lignes:
        par_ipp[ligne["n_ipp"]].append(ligne)
    return par_ipp


def _injecter_champs_manquants(
    lignes_patients: list[dict], entrees: dict[str, dict], generateur: np.random.Generator
) -> tuple[list[dict], list[dict]]:
    taux_final = entrees["taux_champs_manquants"]["valeur"]
    par_ipp = _regrouper_par_ipp(lignes_patients)
    n_ipp_tries = sorted(par_ipp.keys())
    n_fiches = len(n_ipp_tries)

    alterations: list[dict] = []
    absences_structurelles: list[dict] = []

    for colonne, taux in taux_final.items():
        deja_manquants = [n_ipp for n_ipp in n_ipp_tries if par_ipp[n_ipp][0][colonne] is None]
        eligibles = [n_ipp for n_ipp in n_ipp_tries if par_ipp[n_ipp][0][colonne] is not None]

        n_cible_total = round(taux * n_fiches)
        n_a_injecter = n_cible_total - len(deja_manquants)
        if n_a_injecter < 0:
            raise ValueError(
                f"taux_champs_manquants['{colonne}'] = {taux} est inferieur au manquant "
                f"structurel deja mesure ({len(deja_manquants)}/{n_fiches}) : un mecanisme "
                "d'injection ne peut qu'ajouter de l'absence, jamais en retirer"
            )

        for n_ipp in deja_manquants:
            absences_structurelles.append(
                {"table": TABLE_PATIENTS, "colonne": colonne, "identifiant": n_ipp}
            )

        retenus = _selectionner(eligibles, n_a_injecter, generateur)
        for n_ipp in retenus:
            avant = par_ipp[n_ipp][0][colonne]
            for ligne in par_ipp[n_ipp]:
                ligne[colonne] = None
            alterations.append(
                {
                    "table": TABLE_PATIENTS,
                    "colonne": colonne,
                    "identifiant": n_ipp,
                    "avant": avant,
                    "apres": None,
                }
            )

    return alterations, absences_structurelles


def _majuscules(valeur: str) -> str:
    return valeur.upper()


def _espaces_multiples(valeur: str, generateur: np.random.Generator) -> str:
    positions_espace = [i for i, c in enumerate(valeur) if c == " "]
    if not positions_espace:
        return valeur + "  "
    position = positions_espace[int(generateur.integers(0, len(positions_espace)))]
    return valeur[:position] + "  " + valeur[position + 1 :]


def _casse_accents(valeur: str) -> str:
    return valeur.lower().translate(_ACCENTS)


def _injecter_defauts_surface(
    lignes_patients: list[dict], entrees: dict[str, dict], generateur: np.random.Generator
) -> list[dict]:
    taux_par_categorie = entrees["taux_defauts_surface"]["valeur"]
    colonne = "adresse"
    par_ipp = _regrouper_par_ipp(lignes_patients)
    disponibles = sorted(par_ipp.keys())

    alterations: list[dict] = []
    for categorie in ("casse_accents", "espaces_multiples", "majuscules"):
        taux = taux_par_categorie[categorie]
        n_cible = round(taux * len(par_ipp))
        retenus = _selectionner(disponibles, n_cible, generateur)
        disponibles = [n_ipp for n_ipp in disponibles if n_ipp not in set(retenus)]

        for n_ipp in retenus:
            avant = par_ipp[n_ipp][0][colonne]
            if categorie == "majuscules":
                apres = _majuscules(avant)
            elif categorie == "espaces_multiples":
                apres = _espaces_multiples(avant, generateur)
            else:
                apres = _casse_accents(avant)
            for ligne in par_ipp[n_ipp]:
                ligne[colonne] = apres
            alterations.append(
                {
                    "table": TABLE_PATIENTS,
                    "colonne": colonne,
                    "identifiant": n_ipp,
                    "avant": avant,
                    "apres": apres,
                    "categorie_surface": categorie,
                }
            )

    return alterations


DATE_ABERRANTE = datetime(1900, 1, 1, 9, 0)


def _injecter_dates_aberrantes(
    lignes_rdv: list[dict], entrees: dict[str, dict], generateur: np.random.Generator
) -> list[dict]:
    taux = entrees["taux_dates_aberrantes"]["valeur"]
    indices = list(range(len(lignes_rdv)))
    n_cible = round(taux * len(lignes_rdv))
    retenus = _selectionner(indices, n_cible, generateur)

    alterations: list[dict] = []
    for indice in retenus:
        ligne = lignes_rdv[indice]
        avant = ligne["date_rendez_vous"]
        ligne["date_rendez_vous"] = DATE_ABERRANTE
        alterations.append(
            {
                "table": TABLE_RDV,
                "colonne": "date_rendez_vous",
                "identifiant": ligne["n_rdv"],
                "avant": avant,
                "apres": DATE_ABERRANTE,
            }
        )
    return alterations


def _injecter_ages_incoherents(
    lignes_patients: list[dict], entrees: dict[str, dict], generateur: np.random.Generator
) -> list[dict]:
    taux = entrees["taux_ages_incoherents"]["valeur"]
    par_ipp = _regrouper_par_ipp(lignes_patients)
    n_ipp_tries = sorted(par_ipp.keys())
    n_cible = round(taux * len(n_ipp_tries))
    retenus = _selectionner(n_ipp_tries, n_cible, generateur)

    alterations: list[dict] = []
    for n_ipp in retenus:
        ligne_reference = par_ipp[n_ipp][0]
        avant = ligne_reference["date_naissance"]
        fiche = ligne_reference["date_attribution"]
        if int(generateur.integers(0, 2)) == 0:
            apres = fiche + timedelta(days=int(generateur.integers(0, 30)))
        else:
            apres = fiche - timedelta(days=121 * 365)
        for ligne in par_ipp[n_ipp]:
            ligne["date_naissance"] = apres
        alterations.append(
            {
                "table": TABLE_PATIENTS,
                "colonne": "date_naissance",
                "identifiant": n_ipp,
                "avant": avant,
                "apres": apres,
            }
        )
    return alterations


def _injecter_rdv_doublon_creneau(
    lignes_rdv: list[dict], entrees: dict[str, dict], generateur: np.random.Generator
) -> tuple[list[dict], list[dict]]:
    taux = entrees["taux_rdv_doublon_creneau"]["valeur"]
    # exclut les rendez-vous honores deja touches par une date aberrante : un doublon copie
    # integralement la ligne source, y compris sa date_rendez_vous -- une source deja
    # aberrante produirait un doublon dont l'identifiant propre n'apparait pourtant pas dans
    # la categorie dates_aberrantes de la verite terrain (mesure avant d'ecrire : c'est
    # exactement ce qui faisait rougir tests/test_rendez_vous.py::test_ordre_des_dates sur
    # une ligne dupliquee avant cette exclusion).
    honores = [
        ligne
        for ligne in lignes_rdv
        if ligne["etat"] == "HO" and ligne["date_rendez_vous"] != DATE_ABERRANTE
    ]
    n_cible = round(taux * len(honores))
    indices = list(range(len(honores)))
    retenus = _selectionner(indices, n_cible, generateur)

    rang_suivant = max(int(ligne["n_rdv"].split("-")[1]) for ligne in lignes_rdv) + 1
    nouvelles_lignes: list[dict] = []
    alterations: list[dict] = []
    for indice in retenus:
        source = honores[indice]
        duplicata = dict(source)
        n_rdv_nouveau = f"RDV-{rang_suivant:07d}"
        rang_suivant += 1
        duplicata["n_rdv"] = n_rdv_nouveau
        duplicata["etat"] = "EI"
        nouvelles_lignes.append(duplicata)
        alterations.append(
            {
                "table": TABLE_RDV,
                "colonne": "n_rdv",
                "identifiant": n_rdv_nouveau,
                "avant": None,
                "apres": source["n_rdv"],
            }
        )
    return nouvelles_lignes, alterations


def _injecter_factures_sans_pec(
    lignes_factures: list[dict],
    lignes_patients: list[dict],
    lignes_pec: list[dict],
    entrees: dict[str, dict],
    generateur: np.random.Generator,
) -> tuple[list[dict], list[dict]]:
    taux = entrees["taux_factures_sans_pec"]["valeur"]
    compagnie_par_ipp = {p["n_ipp"]: p["compagnie_assurance"] for p in lignes_patients}
    n_couvertes = sum(1 for f in lignes_factures if compagnie_par_ipp[f["n_ipp"]] != "SANS")

    cles_pec = {pec["n_episode"] for pec in lignes_pec}
    n_deja_sans_pec = sum(
        1
        for f in lignes_factures
        if compagnie_par_ipp[f["n_ipp"]] != "SANS" and f["n_episode"] not in cles_pec
    )

    n_cible_total = round(taux * n_couvertes)
    n_a_injecter = n_cible_total - n_deja_sans_pec
    if n_a_injecter < 0:
        raise ValueError(
            f"taux_factures_sans_pec = {taux} est inferieur a la part structurelle deja "
            f"mesuree ({n_deja_sans_pec}/{n_couvertes}) : un mecanisme d'injection ne peut "
            "qu'ajouter des cas, jamais en retirer"
        )

    indices_accordees = [i for i, pec in enumerate(lignes_pec) if pec["etat"] == "O"]
    retenus = _selectionner(indices_accordees, n_a_injecter, generateur)

    factures_par_episode = {f["n_episode"]: f for f in lignes_factures}
    alterations: list[dict] = []
    lignes_pec_conservees: list[dict] = []
    indices_retenus = set(retenus)
    for indice, pec in enumerate(lignes_pec):
        if indice not in indices_retenus:
            lignes_pec_conservees.append(pec)
            continue
        facture = factures_par_episode[pec["n_episode"]]
        facture["part_organisme"] = 0.0
        facture["part_patient"] = facture["montant_total"]
        alterations.append(
            {
                "table": TABLE_FACTURES,
                "colonne": "prise_en_charge",
                "identifiant": facture["n_facture"],
                "avant": pec["n_prise_en_charge"],
                "apres": None,
            }
        )

    return lignes_pec_conservees, alterations


def injecter_defauts(
    lignes: dict[str, list[dict]],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> dict[str, list[dict]]:
    entrees = _entrees(entrees)

    alterations_champs, absences_structurelles = _injecter_champs_manquants(
        lignes[TABLE_PATIENTS], entrees, generateur
    )
    alterations_surface = _injecter_defauts_surface(lignes[TABLE_PATIENTS], entrees, generateur)
    alterations_ages = _injecter_ages_incoherents(lignes[TABLE_PATIENTS], entrees, generateur)

    alterations_dates = _injecter_dates_aberrantes(lignes[TABLE_RDV], entrees, generateur)
    nouvelles_lignes_rdv, alterations_rdv = _injecter_rdv_doublon_creneau(
        lignes[TABLE_RDV], entrees, generateur
    )
    lignes[TABLE_RDV] = lignes[TABLE_RDV] + nouvelles_lignes_rdv

    lignes_pec_conservees, alterations_factures = _injecter_factures_sans_pec(
        lignes[TABLE_FACTURES], lignes[TABLE_PATIENTS], lignes[TABLE_PEC], entrees, generateur
    )
    lignes[TABLE_PEC] = lignes_pec_conservees

    return {
        "champs_manquants": alterations_champs,
        "absence_structurelle": absences_structurelles,
        "defauts_surface": alterations_surface,
        "dates_aberrantes": alterations_dates,
        "ages_incoherents": alterations_ages,
        "rdv_doublon_creneau": alterations_rdv,
        "factures_sans_pec": alterations_factures,
    }
