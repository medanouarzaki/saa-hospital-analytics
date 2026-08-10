"""Génère la table des prises en charge depuis les factures et les patients existants.

Une prise en charge se rattache à une facture, une facture en a au plus une : elle n'existe
que pour un patient couvert (`compagnie_assurance` différent de `SANS`) dont la demande a
effectivement eu lieu (`taux_demande_par_type_episode`). Le registre des champs ne porte
qu'une seule colonne de date pour cette table, `date_verification` — aucune colonne distincte
pour la date de la demande elle-même : la date de facture sert de point de départ implicite
de la démarche, `date_verification` porte la date de décision (conforme à sa propre note).
Une décision qui, ajoutée au délai tiré, dépasserait la fin de la période produit une demande
encore en instance, sans date de vérification. L'état retient les trois codes déjà écrits de
`nomenclature_etat_prise_en_charge` (O, F, N) comme équivalents fonctionnels d'une demande
accordée, refusée ou en instance — le motif de refus n'est pas matérialisé, aucune colonne du
registre ne le porte (voir la note du paramètre correspondant).

Corrige en place `part_organisme` et `part_patient` de la facture rattachée pour toute
demande accordée : c'est la direction unique retenue pour l'accord entre les deux tables
(§4.3 du rapport), la prise en charge gouverne, la facture déjà écrite est corrigée après
coup plutôt que l'inverse. Ne tire aucun nombre en dehors du générateur reçu en argument.
"""

from datetime import date, datetime, time, timedelta

import numpy as np

from generator import config

TABLE = "source.prises_en_charge"


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _tirage_pondere_dict(poids_par_code: dict[str, float], generateur: np.random.Generator) -> str:
    codes = list(poids_par_code.keys())
    poids = np.array([poids_par_code[c] for c in codes], dtype=float)
    poids = poids / poids.sum()
    return codes[int(generateur.choice(len(codes), p=poids))]


def generer_lignes(
    lignes_factures: list[dict],
    lignes_patients: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> list[dict]:
    entrees = _entrees(entrees)

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    taux_demande = entrees["taux_demande_par_type_episode"]["valeur"]
    taux_refus = entrees["taux_refus_prise_en_charge"]["valeur"]
    correspondance_regime = entrees["correspondance_regime_compagnie_assurance"]["valeur"]
    taux_hospitalisation = entrees["taux_part_organisme_hospitalisation"]["valeur"]
    taux_ambulatoire_haut = entrees["taux_part_organisme_ambulatoire_haut"]["valeur"]
    seuil_ambulatoire = entrees["seuil_dirhams_part_organisme_ambulatoire"]["valeur"]
    delai_decision = entrees["delai_jours_decision_prise_en_charge"]["valeur"]
    gabarit_pec = entrees["gabarit_identifiant_prise_en_charge"]["valeur"]

    patients_par_ipp = {p["n_ipp"]: p for p in lignes_patients}

    lignes: list[dict] = []
    rang = 0

    for facture in lignes_factures:
        patient = patients_par_ipp[facture["n_ipp"]]
        compagnie = patient["compagnie_assurance"]
        if compagnie == "SANS":
            continue
        organisme = correspondance_regime[compagnie]

        if generateur.random() >= taux_demande[facture["type_episode"]]:
            continue

        # regle S-18 : prise en charge totale en hospitalisation, ticket moderateur en
        # ambulatoire (CE, UR) au-dela d'un seuil de montant, aucune prise en charge en
        # deca -- remplace un taux par organisme, ecart declare a S-18 corrige par ce lot.
        if facture["type_episode"] == "HOS":
            taux_couverture = taux_hospitalisation
        elif facture["montant_total"] > seuil_ambulatoire:
            taux_couverture = taux_ambulatoire_haut
        else:
            taux_couverture = 0.0
        delai = int(_tirage_pondere_dict(delai_decision, generateur))
        date_decision = facture["date_facture"] + timedelta(days=delai)

        if date_decision > date_fin:
            etat = "N"
            date_verification = None
        elif generateur.random() < taux_refus:
            etat = "F"
            date_verification = datetime.combine(date_decision, time(11, 0))
        else:
            etat = "O"
            date_verification = datetime.combine(date_decision, time(11, 0))
            montant_pris_en_charge = round(facture["montant_total"] * taux_couverture, 2)
            facture["part_organisme"] = montant_pris_en_charge
            facture["part_patient"] = round(facture["montant_total"] - montant_pris_en_charge, 2)

        n_prise_en_charge = gabarit_pec.format(rang=rang)
        rang += 1

        date_reference = (
            date_verification.date() if date_verification is not None else facture["date_facture"]
        )

        lignes.append(
            {
                "n_prise_en_charge": n_prise_en_charge,
                "n_ipp": facture["n_ipp"],
                "n_episode": facture["n_episode"],
                "type_episode": facture["type_episode"],
                "organisme": organisme,
                "n_assure": f"ASS-{facture['n_ipp']}",
                "date_verification": date_verification,
                "etat": etat,
                "taux_prise_en_charge": taux_couverture,
                "date_extraction": max(date_reference, date_debut),
            }
        )

    return lignes
