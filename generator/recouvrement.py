"""Génère les tables d'encaissements, de créances et de relances depuis les factures.

Un dû se décompose par débiteur (organisme, patient) dès la facture elle-même
(`part_organisme`, `part_patient`) : le taux de recouvrement, propre à chaque type
d'épisode, s'applique séparément à chaque part, ce qui garantit par construction qu'aucun
débiteur n'est jamais crédité au-delà de son propre dû. Le registre des champs ne porte
aucune colonne débiteur sur `source.encaissements` ; le débiteur s'y déduit du mode de
règlement (`correspondance_debiteur_mode_reglement`) plutôt que d'une colonne supplémentaire.

Une créance naît d'un dû non soldé au-delà de `seuil_jours_anciennete_creance`, avec l'état
du recouvrement à cette date. Toute nouvelle décision de dette, initiale ou consécutive à une
relance, respecte la même règle jamais-plus-que-dû. La table est une dimension à évolution
lente, sur le même principe que la fiche patient : une créance ne réapparaît dans une
nouvelle partition que lorsque son état change réellement (un versement supplémentaire),
jamais sur un rythme quotidien fixe — voir la note de `seuil_jours_anciennete_creance`.

Une relance ne se déclenche que sur une créance encore ouverte, au montant restant supérieur
au seuil configuré. Une relance aboutie (résultat PAYE ou PART) engendre l'encaissement
correspondant, jamais l'inverse : c'est le résultat de la relance qui gouverne
l'encaissement à générer, conformément à la direction retenue et documentée en
configuration. Ne tire aucun nombre en dehors du générateur reçu en argument.
"""

from datetime import date, datetime, time, timedelta

import numpy as np

from generator import config

TABLE_ENCAISSEMENTS = "source.encaissements"
TABLE_CREANCES = "source.creances"
TABLE_RELANCES = "source.relances"


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


def _decouper_montant(
    montant: float, n_parts: int, generateur: np.random.Generator, montant_minimal: float
) -> list[float]:
    if n_parts == 1:
        return [round(montant, 2)]
    poids = generateur.dirichlet(np.ones(n_parts))
    parts = [round(montant * p, 2) for p in poids[:-1]]
    parts.append(round(montant - sum(parts), 2))
    # absorbe toute part sous le seuil minimal dans une part voisine plutot que de la
    # produire telle quelle : la somme des parts reste inchangee, seule leur repartition
    # en nombre de lignes change.
    fusionne = True
    while fusionne and len(parts) > 1:
        fusionne = False
        for i, part in enumerate(parts):
            if part < montant_minimal:
                voisin = i - 1 if i > 0 else i + 1
                parts[voisin] = round(parts[voisin] + part, 2)
                del parts[i]
                fusionne = True
                break
    return parts


def generer_lignes(
    lignes_factures: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    entrees = _entrees(entrees)

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])

    taux_recouvrement = entrees["taux_recouvrement"]["valeur"]
    repartition_modes = entrees["repartition_modes_reglement"]["valeur"]
    correspondance_debiteur = entrees["correspondance_debiteur_mode_reglement"]["valeur"]
    part_partiels = entrees["part_encaissements_partiels"]["valeur"]
    loi_n_versements = entrees["loi_nombre_versements"]["valeur"]
    delai_patient = entrees["delai_jours_encaissement_patient"]["valeur"]
    delai_organisme = entrees["delai_jours_encaissement_organisme"]["valeur"]
    seuil_jours_creance = entrees["seuil_jours_anciennete_creance"]["valeur"]
    seuil_montant_relance = entrees["seuil_montant_relance"]["valeur"]
    loi_n_relances = entrees["loi_nombre_relances_par_creance"]["valeur"]
    delai_relances = entrees["delai_jours_entre_relances"]["valeur"]
    repartition_canaux = entrees["repartition_canaux_relance"]["valeur"]
    repartition_resultats = entrees["repartition_resultats_relance"]["valeur"]
    repartition_motifs = entrees["repartition_motifs_non_recouvrement"]["valeur"]
    comptes_regisseurs = entrees["comptes_regisseurs"]["valeur"]
    gabarit_encaissement = entrees["gabarit_identifiant_encaissement"]["valeur"]
    gabarit_creance = entrees["gabarit_identifiant_creance"]["valeur"]
    gabarit_relance = entrees["gabarit_identifiant_relance"]["valeur"]
    montant_minimal = entrees["montant_minimal_encaissement"]["valeur"]

    modes_patient = [m for m, d in correspondance_debiteur.items() if d == "PATIENT"]
    poids_modes_patient = {m: repartition_modes[m] for m in modes_patient}

    rang_enc = 0
    rang_cre = 0
    rang_rel = 0

    lignes_enc: list[dict] = []
    lignes_cre: list[dict] = []
    lignes_rel: list[dict] = []

    for facture in lignes_factures:
        n_facture = facture["n_facture"]
        date_facture = facture["date_facture"]
        taux = taux_recouvrement[facture["type_episode"]]

        dus = {"PATIENT": facture["part_patient"], "ORGANISME": facture["part_organisme"]}
        versements: list[tuple[str, float, date]] = []  # (debiteur, montant, date)

        for debiteur, du in dus.items():
            if du <= 0:
                continue
            # recouvrement tout-ou-rien par debiteur : integralement recouvre avec
            # probabilite taux, jamais recouvre sinon - l'esperance du montant recouvre sur
            # l'ensemble des factures d'une categorie egale alors exactement le taux
            # configure, sans que chaque facture ne porte individuellement un solde partiel
            # permanent (ce qu'une fraction fixe appliquee facture par facture produirait :
            # mesure avant d'etre ecartee, voir le rapport, 20212 creances sur 21560
            # factures avec cette premiere approche).
            if generateur.random() >= taux:
                continue
            encaisse = round(du, 2)
            if encaisse <= 0:
                continue

            n_parts = 1
            if generateur.random() < part_partiels:
                n_parts = int(_tirage_pondere_dict(loi_n_versements, generateur))
            montants = _decouper_montant(encaisse, n_parts, generateur, montant_minimal)

            # le seuil minimal peut avoir fusionne des parts : autant de delais que de
            # montants effectivement produits, jamais que de versements demandes au depart
            loi_delai = delai_patient if debiteur == "PATIENT" else delai_organisme
            delais = sorted(
                int(_tirage_pondere_dict(loi_delai, generateur)) for _ in range(len(montants))
            )

            for montant, delai in zip(montants, delais, strict=True):
                if montant <= 0:
                    continue
                jour = date_facture + timedelta(days=delai)
                if jour > date_fin:
                    jour = date_fin
                versements.append((debiteur, montant, jour))

        # facture entierement soldee des lors que le recouvre initial couvre le du total
        montant_encaisse_initial = sum(m for _, m, _ in versements)
        billet_sortie_delivre = montant_encaisse_initial >= round(facture["montant_total"], 2)

        for debiteur, montant, jour in versements:
            mode = (
                "VIR"
                if debiteur == "ORGANISME"
                else _tirage_pondere_dict(poids_modes_patient, generateur)
            )
            lignes_enc.append(
                {
                    "n_encaissement": gabarit_encaissement.format(rang=rang_enc),
                    "n_facture": n_facture,
                    "date_encaissement": datetime.combine(jour, time(10, 0)),
                    "mode_reglement": mode,
                    "montant": montant,
                    "regisseur": _tirage_uniforme_liste(comptes_regisseurs, generateur),
                    "billet_sortie_delivre": billet_sortie_delivre,
                    "date_extraction": max(jour, date_debut),
                }
            )
            rang_enc += 1

        # naissance de creance : dus non soldes au-dela du seuil d'anciennete
        naissance = date_facture + timedelta(days=seuil_jours_creance)
        if naissance > date_fin:
            continue

        restant = {"PATIENT": dus["PATIENT"], "ORGANISME": dus["ORGANISME"]}
        for debiteur, montant, jour in versements:
            if jour <= naissance:
                restant[debiteur] = round(restant[debiteur] - montant, 2)

        montant_restant = round(restant["PATIENT"] + restant["ORGANISME"], 2)
        if montant_restant <= 0:
            continue

        type_debiteur = (
            facture["type_facture"] if restant["ORGANISME"] >= restant["PATIENT"] else "PART"
        )
        motif = _tirage_pondere_dict(repartition_motifs, generateur)
        montant_recouvre_cumule = round(facture["montant_total"] - montant_restant, 2)

        # une creance qui atteint zero est ecrite dans son etat final (motif RCV, montant
        # restant nul), jamais retiree : la contraindre a ne jamais naitre a zero (verifie
        # plus haut) est une chose, lui interdire d'atteindre zero en est une autre - la
        # premiere version confondait les deux, ce qui faisait disparaitre de la
        # table toute relance ayant reellement solde sa creance (mesure avant d'ecrire,
        # voir le rapport).
        instantanes: list[dict] = [
            {
                "n_facture": n_facture,
                "date_naissance_creance": naissance,
                "montant_du": round(facture["montant_total"], 2),
                "montant_recouvre": montant_recouvre_cumule,
                "montant_restant": montant_restant,
                "type_debiteur": type_debiteur,
                "motif_non_recouvrement": motif,
                "date_extraction": max(naissance, date_debut),
            }
        ]
        encaissements_relances: list[dict] = []
        relances_creance: list[dict] = []
        soldee = False

        versements_posterieurs = sorted(
            (jour, debiteur, montant) for debiteur, montant, jour in versements if jour > naissance
        )
        for jour, debiteur, montant in versements_posterieurs:
            if soldee:
                break
            reduction = min(montant, restant[debiteur])
            if reduction <= 0:
                continue
            restant[debiteur] = round(restant[debiteur] - reduction, 2)
            montant_restant = round(montant_restant - reduction, 2)
            montant_recouvre_cumule = round(montant_recouvre_cumule + reduction, 2)
            if montant_restant <= 0:
                soldee = True
            instantanes.append(
                {
                    "n_facture": n_facture,
                    "date_naissance_creance": naissance,
                    "montant_du": round(facture["montant_total"], 2),
                    "montant_recouvre": montant_recouvre_cumule,
                    "montant_restant": max(montant_restant, 0.0),
                    "type_debiteur": type_debiteur,
                    "motif_non_recouvrement": "RCV" if soldee else motif,
                    "date_extraction": max(jour, date_debut),
                }
            )

        if not soldee and montant_restant >= seuil_montant_relance:
            n_relances_max = int(_tirage_pondere_dict(loi_n_relances, generateur))
            for i in range(1, n_relances_max + 1):
                if montant_restant < seuil_montant_relance:
                    break
                date_relance = naissance + timedelta(days=i * delai_relances)
                if date_relance > date_fin:
                    break

                canal = _tirage_pondere_dict(repartition_canaux, generateur)
                resultat = _tirage_pondere_dict(repartition_resultats, generateur)
                relances_creance.append(
                    {
                        "date_relance": date_relance,
                        "canal": canal,
                        "resultat": resultat,
                        "date_extraction": max(date_relance, date_debut),
                    }
                )

                if resultat not in ("PAYE", "PART"):
                    continue

                # une relance aboutie engendre l'encaissement correspondant, jamais
                # l'inverse ; reparti entre les debiteurs encore en reste, proportionnellement
                fraction = 1.0 if resultat == "PAYE" else 0.5
                jour_encaissement = min(date_relance, date_fin)
                for debiteur in ("PATIENT", "ORGANISME"):
                    if restant[debiteur] <= 0:
                        continue
                    part = round(restant[debiteur] * fraction, 2)
                    if part <= 0:
                        continue
                    mode = (
                        "VIR"
                        if debiteur == "ORGANISME"
                        else _tirage_pondere_dict(poids_modes_patient, generateur)
                    )
                    encaissements_relances.append(
                        {
                            "n_facture": n_facture,
                            "date_encaissement": datetime.combine(jour_encaissement, time(10, 0)),
                            "mode_reglement": mode,
                            "montant": part,
                            "billet_sortie_delivre": resultat == "PAYE",
                            "date_extraction": max(jour_encaissement, date_debut),
                        }
                    )
                    restant[debiteur] = round(restant[debiteur] - part, 2)
                    montant_restant = round(montant_restant - part, 2)
                    montant_recouvre_cumule = round(montant_recouvre_cumule + part, 2)

                if montant_restant <= 0:
                    soldee = True
                instantanes.append(
                    {
                        "n_facture": n_facture,
                        "date_naissance_creance": naissance,
                        "montant_du": round(facture["montant_total"], 2),
                        "montant_recouvre": montant_recouvre_cumule,
                        "montant_restant": max(montant_restant, 0.0),
                        "type_debiteur": type_debiteur,
                        "motif_non_recouvrement": "RCV" if soldee else motif,
                        "date_extraction": max(jour_encaissement, date_debut),
                    }
                )
                if soldee:
                    break

        for enc in encaissements_relances:
            enc["n_encaissement"] = gabarit_encaissement.format(rang=rang_enc)
            enc["regisseur"] = _tirage_uniforme_liste(comptes_regisseurs, generateur)
            lignes_enc.append(enc)
            rang_enc += 1

        n_creance = gabarit_creance.format(rang=rang_cre)
        rang_cre += 1
        for instantane in instantanes:
            instantane["n_creance"] = n_creance
            lignes_cre.append(instantane)
        for relance in relances_creance:
            relance["n_relance"] = gabarit_relance.format(rang=rang_rel)
            relance["n_creance"] = n_creance
            lignes_rel.append(relance)
            rang_rel += 1

    return lignes_enc, lignes_cre, lignes_rel
