"""Étude d'ablation : quantifie ce que la performance du modèle complet
doit à des régularités CRÉÉES PAR LE GÉNÉRATEUR de données synthétiques et
qui ne se reproduiraient pas telles quelles dans un système hospitalier
réel.

Quatre variantes, chacune RÉESTIMÉE de bout en bout avec les mêmes graine,
mêmes règles de blocage (INCHANGÉES — voir linkage.modele.comparaisons et
linkage.blocage.regles_blocage, qui ne dépend jamais des comparaisons) et
mêmes sessions EM que le modèle complet, puis prédite sur le même ensemble
de paires candidates :
  - COMPLET : le modèle du dépôt, tel quel ;
  - A : sans les six champs recopiés tels quels par le générateur d'un
    enregistrement à son doublon (nom_famille_1, nom_famille_2, nom_pere,
    nom_mere, quartier, ville) ;
  - B : avec le niveau d'absence à sens unique de la pièce d'identité
    neutralisé (is_null_level=True, aucune preuve) ;
  - C : les deux retraits simultanément.

Ce module N'ÉCRIT DANS AUCUNE TABLE du schéma linkage : les modèles
d'ablation ne sont jamais persistés dans linkage/modele_estime.json (qui
reste le modèle complet du dépôt), seuls les résultats agrégés sont
écrits, dans linkage/ablation.csv, un fichier versionné tabulaire — pas de
sortie binaire.

LIMITE DE L'ÉTUDE, assumée : le blocage étant tenu identique sur les
quatre variantes (condition nécessaire pour que les ensembles de paires
candidates restent comparables), cette étude NE MESURE PAS l'effet que la
perte de ces champs aurait sur la CONSTRUCTION même de l'ensemble
candidat — un champ retiré des comparaisons reste présent dans les
colonnes de blocage. Cet effet serait vraisemblablement plus sévère : deux
des quatre règles de blocage retenues (linkage.blocage.regle_nom_famille_telephone,
regle_nom_famille_adresse, regle_parents_date_naissance) consomment
justement des champs que la variante A retire des comparaisons.
"""

import csv
import time
from pathlib import Path

import pandas as pd
from splink import Linker, SettingsCreator
from splink.backends.duckdb import DuckDBAPI

from linkage.blocage import regle_parents_date_naissance, regle_piece_identite, regles_blocage
from linkage.champs import COMPARAISONS
from linkage.estimation import (
    COLONNE_VILLE,
    GRAINE_ECHANTILLONNAGE_U,
    RAPPEL_HYPOTHESE_PROBABILITE_A_PRIORI,
    REGLE_DETERMINISTE_PROBABILITE_A_PRIORI,
    REGLES_SESSIONS_EM,
    TAILLE_ECHANTILLON_U,
    table_frequence_ville,
)
from linkage.evaluation import (
    SEUIL_PROBABILITE,
    baseline_paires,
    grille_seuils_etendue,
    grille_seuils_mode_bas,
    grille_seuils_requise,
    metriques_paire,
    paires_verite_terrain_presentes,
)
from linkage.modele import comparaisons
from linkage.population import extraire_population
from linkage.regroupement import (
    composantes_connexes,
    metrique_grappe,
    partition_verite_terrain,
)

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_CSV = RACINE / "linkage" / "ablation.csv"

# Les six champs copiés verbatim par le générateur d'un enregistrement à
# son doublon (mesuré séparément : 100% d'accord sur les paires vraies,
# environ 5% de chances d'accord fortuit) — voir la docstring du module.
CHAMPS_RECOPIES_PAR_LE_GENERATEUR = frozenset(
    {"nom_famille_1", "nom_famille_2", "nom_pere", "nom_mere", "quartier", "ville"}
)

# Association règle EM -> comparaisons qu'elle ne peut PAS estimer (ce sont
# les colonnes sur lesquelles elle bloque : tous les enregistrements d'un
# même bloc s'y accordent par construction, l'EM n'y observe donc aucun
# désaccord informatif). Utilisée uniquement pour la vérification de
# couverture EM : dérivée des règles réellement utilisées par
# REGLES_SESSIONS_EM, jamais recopiée séparément.
_COMPARAISONS_BLOQUEES_PAR_REGLE = {
    regle_piece_identite: frozenset({"piece_identite"}),
    regle_parents_date_naissance: frozenset({"nom_pere", "nom_mere", "date_naissance"}),
}

VARIANTES: dict[str, dict] = {
    "complet": {"exclure": frozenset(), "neutraliser_absence_piece_identite": False},
    "A_sans_champs_recopies": {
        "exclure": CHAMPS_RECOPIES_PAR_LE_GENERATEUR,
        "neutraliser_absence_piece_identite": False,
    },
    "B_absence_piece_identite_neutralisee": {
        "exclure": frozenset(),
        "neutraliser_absence_piece_identite": True,
    },
    "C_les_deux_retraits": {
        "exclure": CHAMPS_RECOPIES_PAR_LE_GENERATEUR,
        "neutraliser_absence_piece_identite": True,
    },
}

COLONNES_CSV = (
    "variante",
    "comparaisons_exclues",
    "absence_piece_identite_neutralisee",
    "nb_comparaisons_presentes",
    "nb_paires_candidates",
    "poids_max_non_vt",
    "poids_min_vt",
    "ecart",
    "vrais_positifs",
    "faux_positifs",
    "faux_negatifs",
    "precision",
    "rappel",
    "f_mesure",
    "grappe_restreint_vraies_retrouvees",
    "grappe_global_vraies_retrouvees",
    "grappe_restreint_sur_fusionnes",
    "grappe_global_sur_fusionnes",
    "f_mesure_max_grille",
    "seuil_f_mesure_max_grille",
    "f_mesure_baseline_collision_exacte",
    "depasse_la_baseline",
)


def verifier_couverture_em(comparaisons_presentes: frozenset[str]) -> frozenset[str]:
    """Comparaisons présentes dans la variante mais estimées par AUCUNE des
    sessions EM (REGLES_SESSIONS_EM). Mesuré à partir des règles
    réellement utilisées, jamais supposé.
    """
    couvertes: set[str] = set()
    for regle in REGLES_SESSIONS_EM:
        bloquees = _COMPARAISONS_BLOQUEES_PAR_REGLE[regle]
        couvertes |= comparaisons_presentes - bloquees
    return frozenset(comparaisons_presentes - couvertes)


def construire_et_estimer_variante(
    population: list[dict],
    exclure: frozenset[str],
    neutraliser_absence_piece_identite: bool,
) -> Linker:
    """Réplique exactement le pipeline de linkage.estimation.estimer_modele
    (mêmes graine, mêmes règles de blocage — inchangées, voir la docstring
    du module —, mêmes sessions EM, importées depuis linkage.estimation,
    jamais recopiées en dur), avec les comparaisons de la variante
    demandée. N'écrit dans aucune table, ne persiste aucun fichier modèle.
    """
    settings = SettingsCreator(
        link_type="dedupe_only",
        comparisons=comparaisons(
            exclure=exclure, neutraliser_absence_piece_identite=neutraliser_absence_piece_identite
        ),
        blocking_rules_to_generate_predictions=regles_blocage(),
        unique_id_column_name="n_ipp",
    )
    df = pd.DataFrame(population)
    linker = Linker(df, settings, DuckDBAPI())
    linker.table_management.register_term_frequency_lookup(
        table_frequence_ville(population), COLONNE_VILLE
    )

    linker.training.estimate_probability_two_random_records_match(
        [REGLE_DETERMINISTE_PROBABILITE_A_PRIORI()],
        recall=RAPPEL_HYPOTHESE_PROBABILITE_A_PRIORI,
    )
    linker.training.estimate_u_using_random_sampling(
        max_pairs=TAILLE_ECHANTILLON_U, seed=GRAINE_ECHANTILLONNAGE_U
    )
    for regle in REGLES_SESSIONS_EM:
        linker.training.estimate_parameters_using_expectation_maximisation(regle())

    return linker


def paires_predites_variante(linker: Linker) -> list[tuple[str, str, float, float]]:
    resultat = linker.inference.predict()
    pdf = resultat.as_pandas_dataframe()
    paires = []
    for ligne in pdf.itertuples(index=False):
        d = ligne._asdict()
        n1, n2 = sorted([d["n_ipp_l"], d["n_ipp_r"]])
        paires.append((n1, n2, float(d["match_probability"]), float(d["match_weight"])))
    return paires


def metriques_variante(
    nom: str,
    paires: list[tuple[str, str, float, float]],
    population: list[dict],
    paires_vt: set[tuple[str, str]],
    partition_vraie: dict[str, str],
    ensemble_restreint: set[str],
    baseline_f_mesure: float,
) -> dict:
    poids_vt = [w for _n1, _n2, _p, w in paires if (_n1, _n2) in paires_vt]
    poids_non_vt = [w for _n1, _n2, _p, w in paires if (_n1, _n2) not in paires_vt]
    poids_max_non_vt = max(poids_non_vt)
    poids_min_vt = min(poids_vt)

    m_seuil = metriques_paire(paires, SEUIL_PROBABILITE, paires_vt)

    paires_pour_regroupement = [(n1, n2, proba) for n1, n2, proba, _poids in paires]
    affectation = composantes_connexes(paires_pour_regroupement, SEUIL_PROBABILITE, population)
    m_grappe_restreint = metrique_grappe(affectation, partition_vraie, ensemble_restreint)
    m_grappe_global = metrique_grappe(affectation, partition_vraie)

    grille = sorted(
        set(grille_seuils_requise())
        | set(grille_seuils_etendue(poids_max_non_vt, poids_min_vt))
        | set(grille_seuils_mode_bas(poids_non_vt))
    )
    f_mesures_grille = [(s, metriques_paire(paires, s, paires_vt)["f_mesure"]) for s in grille]
    seuil_f_max, f_max = max(((s, f) for s, f in f_mesures_grille), key=lambda t: t[1])

    return {
        "variante": nom,
        "nb_paires_candidates": len(paires),
        "poids_max_non_vt": poids_max_non_vt,
        "poids_min_vt": poids_min_vt,
        "ecart": poids_min_vt - poids_max_non_vt,
        **m_seuil,
        "grappe_restreint_vraies_retrouvees": m_grappe_restreint["vraies_retrouvees"],
        "grappe_global_vraies_retrouvees": m_grappe_global["vraies_retrouvees"],
        "grappe_restreint_sur_fusionnes": m_grappe_restreint["enregistrements_sur_fusionnes"],
        "grappe_global_sur_fusionnes": m_grappe_global["enregistrements_sur_fusionnes"],
        "f_mesure_max_grille": f_max,
        "seuil_f_mesure_max_grille": seuil_f_max,
        "f_mesure_baseline_collision_exacte": baseline_f_mesure,
        "depasse_la_baseline": m_seuil["f_mesure"] >= baseline_f_mesure,
    }


def ecrire_csv(lignes: list[dict], chemin: Path = CHEMIN_CSV) -> int:
    with chemin.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(COLONNES_CSV)
        for ligne in lignes:
            ecrivain.writerow(
                [
                    ligne["variante"],
                    ",".join(sorted(ligne["comparaisons_exclues"])),
                    ligne["absence_piece_identite_neutralisee"],
                    ligne["nb_comparaisons_presentes"],
                    ligne["nb_paires_candidates"],
                    ligne["poids_max_non_vt"],
                    ligne["poids_min_vt"],
                    ligne["ecart"],
                    ligne["vrais_positifs"],
                    ligne["faux_positifs"],
                    ligne["faux_negatifs"],
                    ligne["precision"],
                    ligne["rappel"],
                    ligne["f_mesure"],
                    ligne["grappe_restreint_vraies_retrouvees"],
                    ligne["grappe_global_vraies_retrouvees"],
                    ligne["grappe_restreint_sur_fusionnes"],
                    ligne["grappe_global_sur_fusionnes"],
                    ligne["f_mesure_max_grille"],
                    ligne["seuil_f_mesure_max_grille"],
                    ligne["f_mesure_baseline_collision_exacte"],
                    ligne["depasse_la_baseline"],
                ]
            )
    return len(lignes)


def dix_paires_vraies_degradees(
    linker_complet: Linker,
    paires_variante: list[tuple[str, str, float, float]],
    paires_vt: set[tuple[str, str]],
    nom_variante: str,
) -> list[dict]:
    """Dix paires de vérité terrain, vraies positives sous le seuil retenu
    dans le modèle complet, devenues des faux négatifs sous ce même seuil
    dans la variante donnée — avec leurs niveaux par comparaison (colonnes
    gamma_*), pour montrer ce que le retrait a coûté.
    """
    predites_variante = {
        (n1, n2) for n1, n2, proba, _poids in paires_variante if proba >= SEUIL_PROBABILITE
    }
    degradees = sorted(paires_vt - predites_variante)[:10]
    if not degradees:
        return []

    resultat = linker_complet.inference.predict()
    pdf = resultat.as_pandas_dataframe()
    lignes = []
    for ligne in pdf.itertuples(index=False):
        d = ligne._asdict()
        n1, n2 = sorted([d["n_ipp_l"], d["n_ipp_r"]])
        if (n1, n2) in degradees:
            niveaux = {
                f"gamma_{nom}": d.get(f"gamma_{nom}") for nom in COMPARAISONS if f"gamma_{nom}" in d
            }
            lignes.append({"n_ipp_1": n1, "n_ipp_2": n2, **niveaux})
    return lignes


def main() -> None:
    population = extraire_population()
    paires_vt = paires_verite_terrain_presentes(population)
    ensemble_restreint: set[str] = set()
    for n1, n2 in paires_vt:
        ensemble_restreint.add(n1)
        ensemble_restreint.add(n2)
    partition_vraie = partition_verite_terrain(population, sorted(paires_vt))

    baseline = baseline_paires()
    paires_baseline_avec_score = [(n1, n2, 1.0, 0.0) for n1, n2 in baseline["union"]]
    baseline_f_mesure = metriques_paire(paires_baseline_avec_score, 0.5, paires_vt)["f_mesure"]

    resultats = []
    resultats_paires = {}
    linker_complet = None
    for nom, parametres in VARIANTES.items():
        exclure = parametres["exclure"]
        neutraliser = parametres["neutraliser_absence_piece_identite"]
        comparaisons_presentes = frozenset(COMPARAISONS.keys()) - exclure

        non_couvertes = verifier_couverture_em(comparaisons_presentes)
        print(f"[{nom}] comparaisons présentes : {sorted(comparaisons_presentes)}")
        if non_couvertes:
            print(
                f"[{nom}] ATTENTION : comparaisons non couvertes par aucune "
                f"session EM : {sorted(non_couvertes)}"
            )
        else:
            print(
                f"[{nom}] couverture EM : toutes les comparaisons présentes "
                "sont estimées par au moins une session"
            )

        t0 = time.time()
        linker = construire_et_estimer_variante(population, exclure, neutraliser)
        print(f"[{nom}] estimation terminée en {time.time() - t0:.2f}s")
        if nom == "complet":
            linker_complet = linker

        paires = paires_predites_variante(linker)
        resultats_paires[nom] = paires

        m = metriques_variante(
            nom,
            paires,
            population,
            paires_vt,
            partition_vraie,
            ensemble_restreint,
            baseline_f_mesure,
        )
        m["comparaisons_exclues"] = exclure
        m["absence_piece_identite_neutralisee"] = neutraliser
        m["nb_comparaisons_presentes"] = len(comparaisons_presentes)
        resultats.append(m)
        print(
            f"[{nom}] paires={m['nb_paires_candidates']} ecart={m['ecart']:.4f} "
            f"f_mesure@{SEUIL_PROBABILITE}={m['f_mesure']:.4f} "
            f"f_mesure_max={m['f_mesure_max_grille']:.4f}@{m['seuil_f_mesure_max_grille']:.6f} "
            f"depasse_baseline={m['depasse_la_baseline']}"
        )

    comptes = {
        nom: m["nb_paires_candidates"] for nom, m in zip(VARIANTES.keys(), resultats, strict=True)
    }
    assert len(set(comptes.values())) == 1, (
        f"le compte de paires candidates diverge entre variantes "
        f"(blocage cense etre identique) : {comptes}"
    )
    print(f"compte de paires candidates, identique sur les quatre variantes : {comptes}")

    nb = ecrire_csv(resultats)
    print(f"{CHEMIN_CSV} : {nb} ligne(s) écrite(s)")

    variante_plus_degradee = min(resultats, key=lambda m: m["f_mesure"])["variante"]
    degradees = dix_paires_vraies_degradees(
        linker_complet, resultats_paires[variante_plus_degradee], paires_vt, variante_plus_degradee
    )
    print(
        f"variante la plus dégradée : {variante_plus_degradee} "
        f"({len(degradees)} paire(s) montrée(s))"
    )
    for d in degradees:
        print(d)


if __name__ == "__main__":
    main()
