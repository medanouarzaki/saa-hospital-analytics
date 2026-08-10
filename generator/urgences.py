"""Génère la table des passages aux urgences depuis les passages de type urgence existants.

Une ligne par passage de catégorie U, exactement, dans l'ordre où ces passages
apparaissent. L'heure d'arrivée est celle déjà tirée par `generator/passages.py` pour le
même passage (non modifiable ce lot), jamais redessinée : l'effet de report post-rupture du
jeûne, déjà porté par le moteur temporel sur le flux « urgences », traverse donc jusqu'à
cette table sans rien y ajouter. Le niveau de tri est modulé par le mode d'arrivée (le mode
SMUR, ambulance médicalisée, sert de substitut au champ d'origine absent du registre des
champs pour cette table — voir la note de `modulateur_origine_tri`), sans jamais déplacer
la répartition globale des niveaux : la distribution conditionnelle au mode non-SMUR est
résolue algébriquement pour que la moyenne pondérée par la part réelle d'arrivées SMUR
reproduise exactement le paramètre. Ne tire aucun nombre en dehors du générateur reçu en
argument.
"""

import math
from datetime import date, datetime, timedelta
from statistics import NormalDist

import numpy as np

from generator import config

TABLE = "source.passages_urgences"


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


def _distributions_tri(
    repartition_globale: dict[str, float], modulateur: dict[str, float], part_smur: float
) -> tuple[dict[str, float], dict[str, float]]:
    # le modulateur redistribue a l'interieur de la repartition globale, il ne la deplace
    # pas : la distribution conditionnelle au mode SMUR est le produit du poids global et
    # du multiplicateur, renormalisee ; la distribution conditionnelle au mode non-SMUR est
    # resolue algebriquement pour que part_smur * smur + (1 - part_smur) * non_smur
    # reproduise exactement repartition_globale, jamais approchee par tirage.
    codes = list(repartition_globale.keys())
    base = np.array([repartition_globale[c] for c in codes])
    boost = np.array([modulateur[c] for c in codes])

    smur_non_norm = base * boost
    smur = smur_non_norm / smur_non_norm.sum()

    non_smur = (base - part_smur * smur) / (1 - part_smur)
    if np.any(non_smur < 0):
        raise ValueError("modulateur_origine_tri trop marque pour la part SMUR configuree")
    non_smur = non_smur / non_smur.sum()

    return dict(zip(codes, smur, strict=True)), dict(zip(codes, non_smur, strict=True))


def _mu_lognormal_pour_quantile(
    cible: float, taux_sous_cible: float, ecart_type_log: float
) -> float:
    # ln(X) ~ Normal(mu, sigma) ; P(X <= cible) = Phi((ln(cible) - mu) / sigma) = taux
    # => mu = ln(cible) - sigma * Phi^-1(taux). Construction exacte, pas un ajustement
    # approche par tirage.
    z = NormalDist().inv_cdf(taux_sous_cible)
    return math.log(cible) - ecart_type_log * z


def generer_lignes(
    lignes_passages: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> list[dict]:
    entrees = _entrees(entrees)

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    repartition_niveaux = entrees["repartition_niveaux_tri"]["valeur"]
    delai_par_niveau = entrees["delai_pec_par_niveau"]["valeur"]
    taux_respect_cible = entrees["taux_respect_cible"]["valeur"]
    orientation = entrees["orientation_urgences"]["valeur"]
    modulateur = entrees["modulateur_origine_tri"]["valeur"]
    repartition_arrivee = entrees["repartition_modes_arrivee"]["valeur"]
    repartition_motifs = entrees["repartition_motifs_recours"]["valeur"]
    repartition_unites = entrees["repartition_unites_hospitalisation"]["valeur"]
    duree_mediane_post_pec_par_orientation = entrees[
        "duree_mediane_minutes_post_prise_en_charge_par_orientation"
    ]["valeur"]
    ecart_type_log_duree = entrees["ecart_type_log_duree_urgences"]["valeur"]
    ecart_type_log_delai = entrees["ecart_type_log_delai_pec"]["valeur"]
    motifs_transfert = [c["code"] for c in entrees["nomenclature_motif_transfert"]["valeur"]]
    taux_consentement_transfert = entrees["taux_consentement_transfert"]["valeur"]
    taux_famille_informee = entrees["taux_famille_informee"]["valeur"]
    taux_inventaire_effets = entrees["taux_inventaire_effets"]["valeur"]

    part_smur = repartition_arrivee["SMUR"]
    distribution_smur, distribution_non_smur = _distributions_tri(
        repartition_niveaux, modulateur, part_smur
    )

    mu_par_niveau = {
        niveau: _mu_lognormal_pour_quantile(cible, taux_respect_cible, ecart_type_log_delai)
        for niveau, cible in delai_par_niveau.items()
    }
    mu_post_pec_par_orientation = {
        orientation: math.log(mediane)
        for orientation, mediane in duree_mediane_post_pec_par_orientation.items()
    }

    lignes_u = [ligne for ligne in lignes_passages if ligne["type_passage"] == "U"]

    lignes: list[dict] = []
    for passage in lignes_u:
        arrivee = passage["date_heure_entree"]

        mode_arrivee = _tirage_pondere_dict(repartition_arrivee, generateur)
        distribution_tri = distribution_smur if mode_arrivee == "SMUR" else distribution_non_smur
        niveau_tri = _tirage_pondere_dict(distribution_tri, generateur)
        motif_recours = _tirage_pondere_dict(repartition_motifs, generateur)

        # arrondies a la seconde : une precision a la microseconde ne correspondrait a
        # aucun systeme d'horodatage reel, et laisserait cette colonne distincte sur
        # chaque ligne par pur artefact du tirage continu, jamais observable dans un jeu
        # de donnees veritable. La seconde, pas la minute, pour ne pas ecraser la cible du
        # niveau le plus grave (1 minute) sous la resolution de l'arrondi lui-meme.
        delai_secondes = max(
            1,
            round(
                60 * float(generateur.lognormal(mu_par_niveau[niveau_tri], ecart_type_log_delai))
            ),
        )
        pec = arrivee + timedelta(seconds=delai_secondes)

        orientation_sortie = _tirage_pondere_dict(orientation, generateur)

        # tiree depuis la prise en charge, jamais depuis l'arrivee, et dependante de
        # l'orientation : voir la note de duree_mediane_minutes_post_prise_en_charge_par_orientation
        # pour l'artefact que cet ordre corrige (une duree totale independante du delai
        # pouvait se trouver plus courte que le delai deja ecoule).
        duree_post_pec_secondes = max(
            1,
            round(
                60
                * float(
                    generateur.lognormal(
                        mu_post_pec_par_orientation[orientation_sortie], ecart_type_log_duree
                    )
                )
            ),
        )
        sortie = pec + timedelta(seconds=duree_post_pec_secondes)
        if sortie.date() > date_fin:
            sortie = datetime.combine(date_fin, datetime.max.time())
            if sortie <= pec:
                pec = sortie - timedelta(minutes=1)

        service_orientation = None
        if orientation_sortie == "HO":
            service_orientation = _tirage_pondere_dict(repartition_unites, generateur)

        motif_transfert = None
        consentement_transfert = None
        if orientation_sortie == "TR":
            motif_transfert = _tirage_uniforme_liste(motifs_transfert, generateur)
            consentement_transfert = bool(generateur.random() < taux_consentement_transfert)

        famille_informee = None
        inventaire_effets = None
        if orientation_sortie == "DC":
            famille_informee = bool(generateur.random() < taux_famille_informee)
            inventaire_effets = bool(generateur.random() < taux_inventaire_effets)

        ligne = {
            "n_passage": passage["n_passage"],
            "n_ipp": passage["n_ipp"],
            "date_heure_arrivee": arrivee,
            "mode_arrivee": mode_arrivee,
            "motif_recours": motif_recours,
            "niveau_tri": niveau_tri,
            "date_heure_pec_medicale": pec,
            "date_heure_sortie": sortie,
            "orientation_sortie": orientation_sortie,
            "service_orientation": service_orientation,
            "motif_transfert": motif_transfert,
            "consentement_transfert": consentement_transfert,
            "famille_informee": famille_informee,
            "inventaire_effets": inventaire_effets,
            "date_extraction": max(arrivee.date(), date_debut),
        }
        lignes.append(ligne)

    return lignes
