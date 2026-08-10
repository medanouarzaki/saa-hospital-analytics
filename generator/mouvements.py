"""Génère la table des mouvements depuis les passages d'hospitalisation existants.

Un séjour correspond à un passage d'hospitalisation et un seul, dans l'ordre où ces
passages apparaissent. Il donne lieu à une ligne d'admission, une ligne de mutation
facultative, puis une ligne de sortie si le passage correspondant en porte une. La durée du
séjour est tirée par ce module, indépendamment de celle déjà tirée par
`generator/passages.py` pour le même passage (non modifiable ce lot) ; sa moyenne, pas sa
médiane, est ajustée pour reproduire le rapport journées d'hospitalisation / admissions
mesuré (voir le rapport), le seul degré de liberté qui reste une fois les admissions et
leur date déjà fixées par le fil des épisodes. Chaque séjour est admis dans l'une des trois
unités d'hospitalisation non chirurgicales ; une mutation change toujours d'unité, jamais
vers celle d'origine. Un lit ne porte jamais deux séjours qui se chevauchent au sein d'une
même unité : l'attribution se fait par un balayage chronologique des occupations, séparé
par unité (chacune sa propre dotation), avec un mécanisme explicite si sa capacité venait à
être dépassée. La part d'admissions de mode urgence est dérivée de la part d'orientation
vers l'hospitalisation des urgences (`orientation_urgences["HO"]`, voir
`generator/config/urgences.yml`), pas tirée indépendamment : les deux décrivent le même
flux et doivent s'accorder en décompte agrégé. `orientation_urgences["HO"]` est une part
des passages aux urgences, une population bien plus large que les admissions
d'hospitalisation elles-mêmes ; le taux appliqué au tirage ci-dessous est recalculé pour
ramener le compte cible (cette part multipliée par le nombre de passages aux urgences) à
une proportion des admissions effectivement fixées par le fil des épisodes, sans quoi les
deux décomptes ne pourraient jamais s'accorder en agrégé. Ne tire aucun nombre en dehors du
générateur reçu en argument.
"""

import math
from datetime import date, datetime, timedelta

import numpy as np

from generator import config, volumes

TABLE = "source.mouvements"
FLUX = "programme"


def _entrees(entrees: dict[str, dict] | None = None) -> dict[str, dict]:
    if entrees is not None:
        return entrees
    return {e["nom"]: e for e in config.charger_entrees()}


def _tirage_pondere_dict(poids_par_code: dict[str, float], generateur: np.random.Generator) -> str:
    codes = list(poids_par_code.keys())
    poids = np.array([poids_par_code[c] for c in codes], dtype=float)
    poids = poids / poids.sum()
    return codes[int(generateur.choice(len(codes), p=poids))]


def _duree_moyenne_cible_jours(lignes_passages_h: list[dict], entrees: dict[str, dict]) -> float:
    # cible mesuree, pas un parametre : le rapport entre les journees d'hospitalisation
    # publiees (proratisees par annee civile, comme les autres volumes) et le nombre
    # d'admissions deja fixe par le fil des episodes.
    journees_annuel = entrees["journees_hospitalisation"]["valeur"]
    annees = sorted({ligne["date_heure_entree"].year for ligne in lignes_passages_h})
    journees_cible = sum(
        journees_annuel * volumes.rapport_annee_partielle(annee, FLUX, entrees) for annee in annees
    )
    return journees_cible / len(lignes_passages_h)


def _mu_lognormal_pour_moyenne(moyenne_cible: float, ecart_type_log: float) -> float:
    # mean(lognormale) = exp(mu + sigma^2/2) ; resoudre mu pour que la moyenne tiree
    # reproduise la cible, plutot que de poser une mediane et laisser la moyenne deriver.
    return math.log(moyenne_cible) - (ecart_type_log**2) / 2


def _attribuer_lits_unite(segments: list[dict], capacite: int, gabarit_lit: str, unite: str) -> int:
    # balayage chronologique par debut de segment (interval scheduling), au sein d'une
    # seule unite : un lit libere par un segment dont la fin precede ou egale le debut du
    # segment courant est reutilise ; a defaut, un lit neuf est pris dans le pool propre a
    # l'unite. Si le pool est deja epuise, mecanisme explicite : le segment en cours dont
    # la fin est la plus tardive est tronque a l'instant du nouveau segment, liberant son
    # lit ; effet mesure et rapporte, jamais applique en silence. Un segment tronque qui
    # porte une mutation planifiee voit cette mutation annulee en cascade (le sejour se
    # termine au point de troncature, il ne peut pas changer d'unite apres coup) : sans
    # cette cascade, le segment de mutation, deja construit avec son propre debut fixe,
    # laisserait une occupation fantome apres la troncature de son predecesseur.
    segments_tries = sorted(segments, key=lambda s: s["debut"])
    lits_libres = list(range(1, capacite + 1))
    occupes: list[tuple[int, dict]] = []
    annules: set[int] = set()
    n_depassements = 0

    for segment in segments_tries:
        if id(segment) in annules:
            continue

        encore_occupes = []
        for lit_id, occ in occupes:
            if occ["fin"] <= segment["debut"]:
                lits_libres.append(lit_id)
            else:
                encore_occupes.append((lit_id, occ))
        occupes = encore_occupes

        if not lits_libres:
            n_depassements += 1
            # candidats a la troncature : jamais un sejour encore ouvert (sans sortie
            # connue du passage correspondant) en priorite, sa fin de balayage tres
            # eloignee (fin de periode) le designerait presque toujours sinon, ce qui
            # forcerait une sortie que le passage ne porte pas ; repli sur l'ensemble des
            # occupes seulement si aucun candidat clos n'est disponible.
            candidats = [
                (lid, o) for lid, o in occupes if o["sejour"]["sortie_visible"] is not None
            ]
            if not candidats:
                candidats = occupes
            lit_id, occ_le_plus_long = max(candidats, key=lambda t: t[1]["fin"])
            occ_le_plus_long["fin"] = segment["debut"]
            occ_le_plus_long["tronque"] = True
            occupes = [(lid, o) for lid, o in occupes if o is not occ_le_plus_long]
            lits_libres.append(lit_id)

            sejour_tronque = occ_le_plus_long["sejour"]
            segment_suivant = sejour_tronque.get("segment_mutation")
            if segment_suivant is not None and segment_suivant is not occ_le_plus_long:
                annules.add(id(segment_suivant))
                sejour_tronque["mutation_ts"] = None
                sejour_tronque["unite_destination"] = None
                sejour_tronque["segment_mutation"] = None

        lit_id = lits_libres.pop(0)
        segment["lit"] = gabarit_lit.format(unite=unite, rang=lit_id)
        occupes.append((lit_id, segment))

    return n_depassements


def _attribuer_lits(
    segments: list[dict], capacite_par_unite: dict[str, int], gabarit_lit: str
) -> int:
    n_depassements = 0
    for unite, capacite in capacite_par_unite.items():
        segments_unite = [s for s in segments if s["unite"] == unite]
        n_depassements += _attribuer_lits_unite(segments_unite, capacite, gabarit_lit, unite)
    return n_depassements


def generer_lignes(
    lignes_passages: list[dict],
    generateur: np.random.Generator,
    entrees: dict[str, dict] | None = None,
) -> tuple[list[dict], int]:
    entrees = _entrees(entrees)

    date_debut = date.fromisoformat(entrees["date_debut"]["valeur"])
    date_fin = date.fromisoformat(entrees["date_fin"]["valeur"])
    gabarit_sejour = entrees["gabarit_identifiant_sejour"]["valeur"]
    gabarit_mouvement = entrees["gabarit_identifiant_mouvement"]["valeur"]
    gabarit_lit = entrees["gabarit_identifiant_lit"]["valeur"]
    part_orientation_ho = entrees["orientation_urgences"]["valeur"]["HO"]
    repartition_sortie = entrees["repartition_mode_sortie"]["valeur"]
    repartition_unites = entrees["repartition_unites_hospitalisation"]["valeur"]
    capacite_par_unite = entrees["capacite_par_unite"]["valeur"]
    part_mutation = entrees["part_sejours_avec_mutation"]["valeur"]
    ecart_type_log = entrees["ecart_type_log_duree_sejour"]["valeur"]

    lignes_h = [ligne for ligne in lignes_passages if ligne["type_passage"] == "H"]
    moyenne_cible_jours = _duree_moyenne_cible_jours(lignes_h, entrees)
    mu = _mu_lognormal_pour_moyenne(moyenne_cible_jours, ecart_type_log)

    # orientation_urgences["HO"] est une part DES PASSAGES AUX URGENCES (population bien
    # plus grande que les admissions d'hospitalisation), pas une part directement
    # applicable aux admissions elles-memes : le nombre cible d'admissions de mode urgence
    # est le nombre de passages aux urgences oriente vers l'hospitalisation, ramene aux
    # admissions effectivement fixees par le fil des episodes -- c'est cette proportion-la,
    # et non part_orientation_ho telle quelle, qui doit gouverner le tirage ci-dessous pour
    # que les deux decomptes s'accordent en agrege.
    n_urgences_total = sum(1 for ligne in lignes_passages if ligne["type_passage"] == "U")
    n_ho_attendu = part_orientation_ho * n_urgences_total
    taux_urgence = n_ho_attendu / len(lignes_h) if lignes_h else 0.0

    # premiere passe : construit chaque sejour (un ou deux segments d'occupation), sans
    # attribuer de lit -- l'attribution se fait globalement par unite, apres coup, sur
    # l'ensemble des segments de la periode, pour que la capacite de chaque unite soit
    # respectee sur toute la periode et non sejour par sejour.
    sejours: list[dict] = []
    segments: list[dict] = []

    for rang, passage in enumerate(lignes_h):
        n_sejour = gabarit_sejour.format(rang=rang)
        admission = passage["date_heure_entree"]
        ferme = passage["date_heure_sortie"] is not None
        unite_admission = _tirage_pondere_dict(repartition_unites, generateur)

        if ferme:
            duree_jours = max(1 / 24, float(generateur.lognormal(mu, ecart_type_log)))
            sortie = admission + timedelta(days=duree_jours)
            if sortie.date() > date_fin:
                sortie = datetime.combine(date_fin, admission.time())
                if sortie <= admission:
                    sortie = admission + timedelta(hours=1)
            fin_balayage = sortie
        else:
            sortie = None
            fin_balayage = datetime.combine(date_fin, datetime.max.time())

        avec_mutation = (
            ferme
            and (fin_balayage - admission) > timedelta(days=1)
            and generateur.random() < part_mutation
        )
        mutation_ts = None
        unite_destination = None
        if avec_mutation:
            fraction = generateur.uniform(0.2, 0.8)
            mutation_ts = admission + (fin_balayage - admission) * fraction
            # une mutation change toujours d'unite : tirage uniforme parmi les unites
            # autres que celle d'origine, jamais celle-ci.
            autres_unites = [u for u in repartition_unites if u != unite_admission]
            unite_destination = autres_unites[int(generateur.integers(0, len(autres_unites)))]

        sejour = {
            "n_sejour": n_sejour,
            "n_ipp": passage["n_ipp"],
            "admission": admission,
            "sortie_visible": sortie,
            "mutation_ts": mutation_ts,
            "unite_admission": unite_admission,
            "unite_destination": unite_destination,
        }
        sejours.append(sejour)

        if mutation_ts is not None:
            segment_1 = {
                "debut": admission,
                "fin": mutation_ts,
                "sejour": sejour,
                "role": "admission",
                "unite": unite_admission,
            }
            segment_2 = {
                "debut": mutation_ts,
                "fin": fin_balayage,
                "sejour": sejour,
                "role": "mutation",
                "unite": unite_destination,
            }
            segments.append(segment_1)
            segments.append(segment_2)
            sejour["segment_admission"] = segment_1
            sejour["segment_mutation"] = segment_2
        else:
            segment_1 = {
                "debut": admission,
                "fin": fin_balayage,
                "sejour": sejour,
                "role": "admission",
                "unite": unite_admission,
            }
            segments.append(segment_1)
            sejour["segment_admission"] = segment_1
            sejour["segment_mutation"] = None

    n_depassements = _attribuer_lits(segments, capacite_par_unite, gabarit_lit)

    lignes: list[dict] = []
    rang_mouvement = 0

    def prochain_n_mouvement() -> str:
        nonlocal rang_mouvement
        rang_mouvement += 1
        return gabarit_mouvement.format(rang=rang_mouvement)

    for sejour in sejours:
        segment_admission = sejour["segment_admission"]
        segment_mutation = sejour["segment_mutation"]

        mode_admission = "U" if generateur.random() < taux_urgence else "O"
        ligne_admission = {
            "n_sejour": sejour["n_sejour"],
            "n_ipp": sejour["n_ipp"],
            "date_heure_admission": sejour["admission"],
            "mode_admission": mode_admission,
            "service_accueil": sejour["unite_admission"],
            "lit": segment_admission["lit"],
            "n_mutation": prochain_n_mouvement(),
            "service_origine": None,
            "service_destination": None,
            "date_heure_mutation": None,
            "date_heure_sortie": None,
            "mode_sortie": None,
            "date_extraction": max(sejour["admission"].date(), date_debut),
        }
        lignes.append(ligne_admission)

        if segment_mutation is not None:
            ligne_mutation = {
                "n_sejour": sejour["n_sejour"],
                "n_ipp": sejour["n_ipp"],
                "date_heure_admission": None,
                "mode_admission": None,
                "service_accueil": None,
                "lit": segment_mutation["lit"],
                "n_mutation": prochain_n_mouvement(),
                "service_origine": sejour["unite_admission"],
                "service_destination": sejour["unite_destination"],
                "date_heure_mutation": sejour["mutation_ts"],
                "date_heure_sortie": None,
                "mode_sortie": None,
                "date_extraction": max(sejour["mutation_ts"].date(), date_debut),
            }
            lignes.append(ligne_mutation)

        if sejour["sortie_visible"] is not None:
            # le segment tronque par le mecanisme de capacite (rare, mesure : jamais sur la
            # generation de reference) redefinit la fin reellement occupee du dernier
            # segment du sejour ; la sortie ecrite doit rester coherente avec cette fin.
            dernier_segment = segment_mutation or segment_admission
            sortie_effective = dernier_segment["fin"]
            mode_sortie = _tirage_pondere_dict(repartition_sortie, generateur)
            ligne_sortie = {
                "n_sejour": sejour["n_sejour"],
                "n_ipp": sejour["n_ipp"],
                "date_heure_admission": None,
                "mode_admission": None,
                "service_accueil": None,
                "lit": None,
                "n_mutation": prochain_n_mouvement(),
                "service_origine": None,
                "service_destination": None,
                "date_heure_mutation": None,
                "date_heure_sortie": sortie_effective,
                "mode_sortie": mode_sortie,
                "date_extraction": max(sortie_effective.date(), date_debut),
            }
            lignes.append(ligne_sortie)

    return lignes, n_depassements
