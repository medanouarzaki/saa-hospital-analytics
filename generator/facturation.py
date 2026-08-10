"""Génère les tables des factures et des lignes de facture depuis les épisodes existants.

Seuls les épisodes d'hospitalisation (HOS) et de consultation externe (CE) sont facturables
(voir la note de `types_episode_facturables` : les urgences ne portent aucun acte de
consultation propre dans la nomenclature des actes, déjà close). Un séjour porte une ligne
par journée réellement occupée, reconstruite depuis `source.mouvements` (admission au
premier jour, sortie effective si le séjour en porte une, sinon fin de période) — jamais
depuis la durée indépendamment tirée par `generator/mouvements.py` lui-même. Les examens de
laboratoire sont d'abord dénombrés par catégorie mesurée non nulle (jamais depuis le total
indépendamment proratisé, qui diffère de la somme des catégories d'une unité par arrondi,
voir le rapport), puis groupés en prélèvements attribués à des créneaux — un par jour de
séjour facturé, un par épisode de consultation facturé — tirés sans remise pour qu'un même
couple (facture, date d'acte) ne porte jamais deux prélèvements distincts. Le montant de
chaque ligne et le montant total de chaque facture appliquent la règle déjà écrite dans
`generator/config/tarification.yml`, jamais recalculée d'une autre façon. Ne tire aucun
nombre en dehors du générateur reçu en argument.
"""

from datetime import date, datetime, time, timedelta

import numpy as np

from generator import config, volumes

TABLE_FACTURES = "source.factures"
TABLE_LIGNES = "source.lignes_facture"

CATEGORIES_LABORATOIRE = {
    "immuno_serologie": "examens_immuno_serologie",
    "hematologie_transfusion": "examens_hematologie_transfusion",
    "chimie_biologie": "examens_chimie_biologie",
}


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


def _construire_sejours(
    lignes_passages: list[dict], lignes_mouvements: list[dict], date_fin: date
) -> dict[str, dict]:
    lignes_h = [p for p in lignes_passages if p["type_passage"] == "H"]
    admissions = [ligne for ligne in lignes_mouvements if ligne["date_heure_admission"] is not None]
    sorties = {
        ligne["n_sejour"]: ligne["date_heure_sortie"]
        for ligne in lignes_mouvements
        if ligne["date_heure_sortie"] is not None
    }

    sejours: dict[str, dict] = {}
    for passage, admission in zip(lignes_h, admissions, strict=True):
        entree = admission["date_heure_admission"]
        sortie = sorties.get(admission["n_sejour"])
        if sortie is None:
            sortie = datetime.combine(date_fin, time.max)
        duree_jours = (sortie - entree).total_seconds() / 86400
        n_journees = max(1, round(duree_jours))
        sejours[passage["n_passage"]] = {
            "n_ipp": passage["n_ipp"],
            "unite": admission["service_accueil"],
            "entree": entree,
            "n_journees": n_journees,
        }
    return sejours


def generer_lignes(
    lignes_passages: list[dict],
    lignes_mouvements: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    entrees = _entrees(entrees)

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    taux_facturation = entrees["taux_facturation"]["valeur"]
    types_facturables = entrees["types_episode_facturables"]["valeur"]
    part_imagerie = entrees["part_episodes_imagerie"]["valeur"]
    loi_n_imagerie = entrees["loi_nombre_actes_imagerie_par_episode"]["valeur"]
    poids_jour_hos = entrees["poids_relatif_prelevement_jour_hospitalisation"]["valeur"]
    poids_ce = entrees["poids_relatif_prelevement_episode_consultation"]["valeur"]
    loi_n_examens = entrees["loi_nombre_examens_par_prelevement"]["valeur"]
    loi_quantite_lab = entrees["loi_quantite_ligne_laboratoire"]["valeur"]
    repartition_types_facture = entrees["repartition_types_facture"]["valeur"]
    repartition_etats_facture = entrees["repartition_etats_facture"]["valeur"]
    delai_emission = entrees["delai_jours_emission_facture"]["valeur"]
    seuil_ambulatoire = entrees["seuil_dirhams_part_organisme_ambulatoire"]["valeur"]
    taux_organisme_haut = entrees["taux_part_organisme_ambulatoire_haut"]["valeur"]
    comptes = entrees["comptes_utilisateurs_facturation"]["valeur"]
    gabarit_facture = entrees["gabarit_identifiant_facture"]["valeur"]

    actes = entrees["nomenclature_actes"]["valeur"]
    actes_par_code = {a["code"]: a for a in actes}
    valeurs_lettres = {
        lettre["code"]: lettre["valeur_unitaire"]
        for lettre in entrees["nomenclature_lettres_cles"]["valeur"]
    }
    diagnostics = [c["code"] for c in entrees["nomenclature_diagnostic"]["valeur"]]

    def montant(code_acte: str, quantite: int) -> float:
        acte = actes_par_code[code_acte]
        return valeurs_lettres[acte["lettre_cle"]] * acte["coefficient"] * quantite

    def acte_pour_activite(code_activite: str) -> str:
        for acte in actes:
            if acte["type_rattachement"] == "activite" and acte["rattachement"] == code_activite:
                return acte["code"]
        raise KeyError(f"aucun acte rattaché à l'activité {code_activite!r}")

    codes_lab_par_categorie = {
        categorie: [a["code"] for a in actes if a["code"].startswith(prefixe)]
        for categorie, prefixe in {
            "immuno_serologie": "LAB-IS-",
            "hematologie_transfusion": "LAB-HT-",
            "chimie_biologie": "LAB-CB-",
        }.items()
    }
    codes_imagerie = [
        a["code"]
        for a in actes
        if a["type_rattachement"] == "service" and a["rattachement"] == "RAD"
    ]

    sejours = _construire_sejours(lignes_passages, lignes_mouvements, date_fin)
    lignes_h = [p for p in lignes_passages if p["type_passage"] == "H"]
    lignes_ce = [p for p in lignes_passages if p["type_passage"] == "C"]

    episodes: list[tuple[str, dict]] = []
    if "HOS" in types_facturables:
        episodes.extend(("HOS", p) for p in lignes_h)
    if "CE" in types_facturables:
        episodes.extend(("CE", p) for p in lignes_ce)

    episodes_factures = [ep for ep in episodes if generateur.random() < taux_facturation]

    # creneaux de prelevement : un par jour de sejour facture (poids poids_jour_hos), un par
    # episode de consultation facture (poids poids_ce). Tires sans remise plus bas, pour
    # qu'un meme couple (facture, date d'acte) ne porte jamais deux prelevements distincts.
    creneaux: list[tuple[float, str, str, date]] = []
    for type_episode, passage in episodes_factures:
        if type_episode == "HOS":
            sejour = sejours[passage["n_passage"]]
            for i in range(sejour["n_journees"]):
                jour = (sejour["entree"] + timedelta(days=i)).date()
                creneaux.append((poids_jour_hos, type_episode, passage["n_passage"], jour))
        else:
            creneaux.append(
                (poids_ce, type_episode, passage["n_passage"], passage["date_heure_entree"].date())
            )

    # examens a repartir : somme des categories mesurees non nulles, proratisees par annee
    # civile independamment (piege deja mesure : diffère du total independamment proratise
    # d'une unite par arrondi -- jamais utilise ici).
    pool_examens: list[str] = []
    for categorie, nom_volume in CATEGORIES_LABORATOIRE.items():
        n = sum(volumes.comptes_journaliers(nom_volume, entrees=entrees).values())
        codes = codes_lab_par_categorie[categorie]
        for _ in range(n):
            pool_examens.append(_tirage_uniforme_liste(codes, generateur))
    pool = np.array(pool_examens, dtype=object)
    generateur.shuffle(pool)

    n_prelevements = 0
    reste = len(pool)
    tailles_groupes: list[int] = []
    while reste > 0:
        taille = min(int(_tirage_pondere_dict(loi_n_examens, generateur)), reste)
        tailles_groupes.append(taille)
        reste -= taille
        n_prelevements += 1

    n_prelevements = min(n_prelevements, len(creneaux))
    tailles_groupes = tailles_groupes[:n_prelevements]

    poids_creneaux = np.array([c[0] for c in creneaux], dtype=float)
    poids_creneaux = poids_creneaux / poids_creneaux.sum()
    indices_choisis = generateur.choice(
        len(creneaux), size=n_prelevements, replace=False, p=poids_creneaux
    )

    examens_par_creneau: dict[tuple[str, date], list[str]] = {}
    curseur = 0
    for indice, taille in zip(indices_choisis, tailles_groupes, strict=True):
        _, _, n_episode, jour = creneaux[int(indice)]
        examens_par_creneau.setdefault((n_episode, jour), []).extend(
            pool[curseur : curseur + taille].tolist()
        )
        curseur += taille

    # imagerie : part_episodes_imagerie des episodes factures, independamment du laboratoire
    imagerie_par_episode: dict[str, list[tuple[str, date]]] = {}
    for type_episode, passage in episodes_factures:
        if generateur.random() >= part_imagerie:
            continue
        n_actes = int(_tirage_pondere_dict(loi_n_imagerie, generateur))
        if type_episode == "HOS":
            sejour = sejours[passage["n_passage"]]
            jours_possibles = [
                (sejour["entree"] + timedelta(days=i)).date() for i in range(sejour["n_journees"])
            ]
        else:
            jours_possibles = [passage["date_heure_entree"].date()]
        lignes_img = []
        for _ in range(n_actes):
            code = _tirage_uniforme_liste(codes_imagerie, generateur)
            jour = _tirage_uniforme_liste(jours_possibles, generateur)
            lignes_img.append((code, jour))
        imagerie_par_episode[passage["n_passage"]] = lignes_img

    lignes_factures: list[dict] = []
    lignes_lignes: list[dict] = []
    rang_facture = 0

    for type_episode, passage in episodes_factures:
        n_episode = passage["n_passage"]
        sous_lignes: list[dict] = []

        if type_episode == "HOS":
            sejour = sejours[n_episode]
            for i in range(sejour["n_journees"]):
                jour = (sejour["entree"] + timedelta(days=i)).date()
                sous_lignes.append(
                    {
                        "code_acte": "HOSP-J",
                        "quantite": 1,
                        "date_acte": jour,
                        "service_executant": sejour["unite"],
                    }
                )
        else:
            code_acte = acte_pour_activite(passage["activite"])
            sous_lignes.append(
                {
                    "code_acte": code_acte,
                    "quantite": 1,
                    "date_acte": passage["date_heure_entree"].date(),
                    "service_executant": "CE",
                }
            )

        for jour, codes_examens in (
            (jour, codes) for (ep, jour), codes in examens_par_creneau.items() if ep == n_episode
        ):
            for code_acte in codes_examens:
                quantite = int(_tirage_pondere_dict(loi_quantite_lab, generateur))
                sous_lignes.append(
                    {
                        "code_acte": code_acte,
                        "quantite": quantite,
                        "date_acte": jour,
                        "service_executant": "LAB",
                    }
                )

        for code_acte, jour in imagerie_par_episode.get(n_episode, []):
            sous_lignes.append(
                {
                    "code_acte": code_acte,
                    "quantite": 1,
                    "date_acte": jour,
                    "service_executant": "RAD",
                }
            )

        if not sous_lignes:
            continue

        n_facture = gabarit_facture.format(rang=rang_facture)
        rang_facture += 1

        date_acte_max = max(sl["date_acte"] for sl in sous_lignes)
        delai = int(_tirage_pondere_dict(delai_emission, generateur))
        date_facture = date_acte_max + timedelta(days=delai)
        if date_facture > date_fin:
            date_facture = date_fin

        montant_total = 0.0
        for rang_ligne, sl in enumerate(sous_lignes, start=1):
            acte = actes_par_code[sl["code_acte"]]
            m = montant(sl["code_acte"], sl["quantite"])
            montant_total += m
            lignes_lignes.append(
                {
                    "n_facture": n_facture,
                    "n_ligne": rang_ligne,
                    "code_acte": sl["code_acte"],
                    "libelle_acte": acte["libelle"],
                    "lettre_cle": acte["lettre_cle"],
                    "coefficient": acte["coefficient"],
                    "quantite": sl["quantite"],
                    "tarif_unitaire": valeurs_lettres[acte["lettre_cle"]],
                    "montant": m,
                    "service_executant": sl["service_executant"],
                    "date_acte": sl["date_acte"],
                    "date_extraction": max(sl["date_acte"], date_debut),
                }
            )

        montant_total = round(montant_total, 2)
        if type_episode == "HOS" or montant_total <= seuil_ambulatoire:
            part_organisme = montant_total
        else:
            part_organisme = round(montant_total * taux_organisme_haut, 2)
        part_patient = round(montant_total - part_organisme, 2)

        ligne_facture = {
            "n_facture": n_facture,
            "n_ipp": passage["n_ipp"],
            "n_episode": n_episode,
            "type_episode": type_episode,
            "code_diagnostic_cim10": _tirage_uniforme_liste(diagnostics, generateur),
            "date_facture": date_facture,
            "type_facture": _tirage_pondere_dict(repartition_types_facture, generateur),
            "service_emetteur": sejours[n_episode]["unite"] if type_episode == "HOS" else "CE",
            "etat": _tirage_pondere_dict(repartition_etats_facture, generateur),
            "montant_total": montant_total,
            "part_organisme": part_organisme,
            "part_patient": part_patient,
            "cree_par": _tirage_uniforme_liste(comptes, generateur),
            "date_creation": datetime.combine(date_facture, time(9, 0)),
            "date_extraction": max(date_facture, date_debut),
        }
        lignes_factures.append(ligne_facture)

    return lignes_factures, lignes_lignes
