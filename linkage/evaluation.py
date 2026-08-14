"""Évaluation du modèle de rapprochement : balayage de seuils, choix du
seuil SANS ÉTIQUETTE, confrontation à la référence par collision exacte,
et peuplement final de linkage.grappes_identite et linkage.evaluation.

Le seuil n'est jamais calibré sur la vérité terrain : il est choisi à
partir de propriétés observables sans étiquette (bimodalité de la
distribution des scores, marge mesurée dans l'espace des poids de
correspondance), puis ÉVALUÉ contre la vérité terrain — jamais l'inverse.
"""

from itertools import combinations
from pathlib import Path

import yaml

from linkage.population import _connexion, extraire_population
from linkage.prediction import construire_linker_pour_prediction
from linkage.regroupement import (
    composantes_connexes,
    metrique_grappe,
    partition_verite_terrain,
    tailles_des_grappes,
)

RACINE = Path(__file__).resolve().parent.parent
VERITE_TERRAIN = RACINE / "generator" / "output" / "scenario_30" / "verite_terrain.yml"

# Seuil retenu (voir le raisonnement complet, sans vérité terrain, en
# amont) : une probabilité de 0,5 (poids de correspondance 0), nettement
# plus proche du mode des paires vraies (17,4 unités de poids) que du mode
# des paires non-vraies (253,5 unités de poids) — le côté haut de la
# marge, où le gain marginal en précision est nul mais où la perte
# marginale en rappel n'a pas encore commencé.
SEUIL_PROBABILITE = 0.5


def paires_verite_terrain_presentes(population: list[dict]) -> set[tuple[str, str]]:
    """Les paires de vérité terrain dont les deux identifiants sont
    présents dans la population courante, dans l'ordre canonique.
    """
    n_ipp_valides = {enregistrement["n_ipp"] for enregistrement in population}
    with VERITE_TERRAIN.open(encoding="utf-8") as f:
        verite_terrain = yaml.safe_load(f)
    paires = verite_terrain["doublons"]["paires"]
    return {
        tuple(sorted([p["n_ipp_1"], p["n_ipp_2"]]))
        for p in paires
        if p["n_ipp_1"] in n_ipp_valides and p["n_ipp_2"] in n_ipp_valides
    }


def paires_predites(population: list[dict] | None = None) -> list[tuple[str, str, float, float]]:
    """(n_ipp_1, n_ipp_2, probabilite, poids_correspondance) pour chaque
    paire candidate, en réexécutant la prédiction EN MÉMOIRE (jamais une
    réestimation, jamais une écriture dans linkage.paires_candidates,
    lue en lecture seule ailleurs dans ce module).
    """
    if population is None:
        population = extraire_population()
    linker = construire_linker_pour_prediction(population)
    df_predict = linker.inference.predict()
    pdf = df_predict.as_pandas_dataframe()
    paires = []
    for ligne in pdf.itertuples(index=False):
        d = ligne._asdict()
        n1, n2 = sorted([d["n_ipp_l"], d["n_ipp_r"]])
        paires.append((n1, n2, float(d["match_probability"]), float(d["match_weight"])))
    return paires


def metriques_paire(
    paires: list[tuple[str, str, float, float]],
    seuil_probabilite: float,
    paires_vt_presentes: set[tuple[str, str]],
) -> dict:
    """TP/FP/FN et précision/rappel/F-mesure au niveau paire, pour un
    seuil de probabilité donné. Le dénominateur du rappel est
    `len(paires_vt_presentes)`, jamais un littéral.
    """
    predites = {(n1, n2) for n1, n2, proba, _poids in paires if proba >= seuil_probabilite}
    vp = len(predites & paires_vt_presentes)
    fp = len(predites - paires_vt_presentes)
    fn = len(paires_vt_presentes - predites)

    precision = vp / (vp + fp) if (vp + fp) else 0.0
    rappel = vp / (vp + fn) if (vp + fn) else 0.0
    f_mesure = 2 * precision * rappel / (precision + rappel) if (precision + rappel) > 0 else 0.0

    return {
        "vrais_positifs": vp,
        "faux_positifs": fp,
        "faux_negatifs": fn,
        "precision": precision,
        "rappel": rappel,
        "f_mesure": f_mesure,
    }


def baseline_paires(environ: dict[str, str] | None = None) -> dict[str, set[tuple[str, str]]]:
    """Reconstruit, par requête sur marts.dim_patient, les paires produites
    par chacun des deux critères de collision exacte de
    dbt/models/marts/agg_doublons_identite.sql, et leur union.
    """
    with _connexion(environ) as connexion, connexion.cursor() as curseur:
        curseur.execute(
            """
            select array_agg(n_ipp order by n_ipp)
            from marts.dim_patient
            where est_courante
              and nom is not null and nom != ''
              and nom_famille_1 is not null and nom_famille_1 != ''
              and date_naissance is not null
            group by nom, nom_famille_1, date_naissance
            having count(*) >= 2
            """
        )
        groupes_nom = curseur.fetchall()

        curseur.execute(
            """
            select array_agg(n_ipp order by n_ipp)
            from marts.dim_patient
            where est_courante
              and type_piece_identite is not null and type_piece_identite != ''
              and n_piece_identite is not null and n_piece_identite != ''
            group by type_piece_identite, n_piece_identite
            having count(*) >= 2
            """
        )
        groupes_piece = curseur.fetchall()

    paires_nom = {
        tuple(sorted(paire)) for (groupe,) in groupes_nom for paire in combinations(groupe, 2)
    }
    paires_piece = {
        tuple(sorted(paire)) for (groupe,) in groupes_piece for paire in combinations(groupe, 2)
    }

    return {
        "nom_date_naissance": paires_nom,
        "piece_identite": paires_piece,
        "union": paires_nom | paires_piece,
    }


def poids_vers_probabilite(poids: float) -> float:
    """Convertit un poids de correspondance (log2 des chances) en
    probabilité : p = 1 / (1 + 2^-poids), la relation standard de la
    bibliothèque entre match_weight et match_probability.
    """
    return 1.0 / (1.0 + 2.0 ** (-poids))


def grille_seuils_requise() -> list[float]:
    """0,50 à 0,99, pas 0,01 — cinquante points, exigés par le périmètre."""
    return [round(0.50 + 0.01 * i, 2) for i in range(50)]


def grille_seuils_mode_bas(poids_non_vt: list[float]) -> list[float]:
    """Au moins cinq points DANS le mode bas (la distribution des poids des
    paires non-vraies elle-même), convertis en probabilité — pas seulement
    entre les deux modes comme le fait `grille_seuils_etendue`. Sans ces
    points, aucun seuil du balayage ne descend assez bas pour qu'un faux
    positif apparaisse jamais : la courbe précision/rappel n'a alors qu'un
    bras (précision egale à 1 partout). Les points sont choisis par
    quantile sur `poids_non_vt`, jamais un littéral de poids.
    """
    poids_tries = sorted(poids_non_vt)
    n = len(poids_tries)
    indices = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1})
    poids_choisis = [poids_tries[i] for i in indices]
    return sorted({poids_vers_probabilite(p) for p in poids_choisis})


def grille_seuils_etendue(poids_max_non_vt: float, poids_min_vt: float) -> list[float]:
    """Grille étendue en ESPACE DE POIDS : au moins dix points entre le
    maximum des paires non-vraies et le minimum des paires vraies, plus
    plusieurs points au-delà de ce minimum, jusqu'à (sans l'atteindre) une
    probabilité de 1,0.
    """
    poids_bas = [
        poids_max_non_vt + (poids_min_vt - poids_max_non_vt) * fraction / 10
        for fraction in range(11)
    ]
    poids_haut = [poids_min_vt + delta for delta in (1, 2, 3, 5, 8, 12, 20, 30, 45, 60)]
    tous_les_poids = sorted(set(poids_bas + poids_haut))
    return sorted({poids_vers_probabilite(p) for p in tous_les_poids})


def balayage(
    paires: list[tuple[str, str, float, float]],
    population: list[dict],
    seuils: list[float],
    paires_vt_presentes: set[tuple[str, str]],
    ensemble_restreint: set[str],
) -> list[dict]:
    """Une ligne par seuil : métriques de paire, métriques de grappe dans
    les deux portées (regroupement écrit à la main, réutilisé pour tous
    les seuils), et le dénominateur (nombre de paires de vérité terrain
    présentes).
    """
    partition_vraie = partition_verite_terrain(population, sorted(paires_vt_presentes))
    lignes = []
    for seuil in seuils:
        m_paire = metriques_paire(paires, seuil, paires_vt_presentes)

        paires_pour_regroupement = [(n1, n2, proba) for n1, n2, proba, _poids in paires]
        affectation = composantes_connexes(paires_pour_regroupement, seuil, population)
        tailles = tailles_des_grappes(affectation)
        nb_grappes_taille2 = sum(1 for t in tailles.values() if t == 2)
        taille_max = max(tailles.values())
        nb_enreg_grappe_gt2 = sum(t for t in tailles.values() if t > 2)

        m_grappe_restreint = metrique_grappe(affectation, partition_vraie, ensemble_restreint)
        m_grappe_global = metrique_grappe(affectation, partition_vraie)

        lignes.append(
            {
                "seuil": seuil,
                **m_paire,
                "nb_paires_verite_terrain": len(paires_vt_presentes),
                "nb_grappes_taille2": nb_grappes_taille2,
                "taille_max_grappe": taille_max,
                "nb_enregistrements_grappe_gt2": nb_enreg_grappe_gt2,
                "nb_grappes_predites": sum(1 for t in tailles.values() if t > 1),
                "grappe_restreint": m_grappe_restreint,
                "grappe_global": m_grappe_global,
            }
        )
    return lignes


COLONNES_CSV_COURBE = (
    "seuil_probabilite",
    "vrais_positifs",
    "faux_positifs",
    "faux_negatifs",
    "precision",
    "rappel",
    "f_mesure",
    "nb_paires_verite_terrain",
    "nb_grappes_predites",
    "nb_grappes_exactes_restreint",
    "nb_grappes_exactes_global",
    "nb_enregistrements_sur_fusionnes_restreint",
    "nb_enregistrements_sur_fusionnes_global",
)


def charger_evaluation(lignes: list[dict], environ: dict[str, str] | None = None) -> int:
    """Vide puis recharge linkage.evaluation avec une ligne par seuil.

    Les colonnes de grappe qui comparent à la partition vraie
    (nb_grappes_exactes_*, nb_enregistrements_sur_fusionnes_*) portent
    désormais les DEUX portées, restreinte et globale, sans ambiguïté de
    nom (voir linkage/ddl/03_evaluation.sql) : plus de portée implicite.
    """
    valeurs = [
        (
            ligne["seuil"],
            ligne["vrais_positifs"],
            ligne["faux_positifs"],
            ligne["faux_negatifs"],
            ligne["precision"],
            ligne["rappel"],
            ligne["f_mesure"],
            ligne["nb_grappes_predites"],
            ligne["grappe_restreint"]["vraies_retrouvees"],
            ligne["grappe_global"]["vraies_retrouvees"],
            ligne["grappe_restreint"]["enregistrements_sur_fusionnes"],
            ligne["grappe_global"]["enregistrements_sur_fusionnes"],
            ligne["nb_paires_verite_terrain"],
        )
        for ligne in lignes
    ]
    with _connexion(environ) as connexion, connexion.cursor() as curseur:
        curseur.execute("truncate table linkage.evaluation")
        curseur.executemany(
            """
            insert into linkage.evaluation
                (seuil, vrais_positifs, faux_positifs, faux_negatifs,
                 precision_valeur, rappel, f_mesure,
                 nb_grappes_predites,
                 nb_grappes_exactes_restreint, nb_grappes_exactes_global,
                 nb_enregistrements_sur_fusionnes_restreint,
                 nb_enregistrements_sur_fusionnes_global,
                 nb_paires_verite_terrain)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            valeurs,
        )
        connexion.commit()
    return len(valeurs)


def ecrire_courbe_csv(lignes: list[dict], chemin: Path) -> int:
    """Écrit la courbe précision/rappel versionnée (linkage/courbe_precision_rappel.csv),
    une ligne par seuil du balayage, avec les deux portées de grappe. Ne lit
    ni n'écrit aucune table : prend les lignes déjà calculées par
    `balayage`, la même source que `charger_evaluation`.
    """
    import csv

    with chemin.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(COLONNES_CSV_COURBE)
        for ligne in lignes:
            ecrivain.writerow(
                [
                    ligne["seuil"],
                    ligne["vrais_positifs"],
                    ligne["faux_positifs"],
                    ligne["faux_negatifs"],
                    ligne["precision"],
                    ligne["rappel"],
                    ligne["f_mesure"],
                    ligne["nb_paires_verite_terrain"],
                    ligne["nb_grappes_predites"],
                    ligne["grappe_restreint"]["vraies_retrouvees"],
                    ligne["grappe_global"]["vraies_retrouvees"],
                    ligne["grappe_restreint"]["enregistrements_sur_fusionnes"],
                    ligne["grappe_global"]["enregistrements_sur_fusionnes"],
                ]
            )
    return len(lignes)


def charger_grappes_identite(
    affectation: dict[str, str],
    tailles: dict[str, int],
    seuil: float,
    environ: dict[str, str] | None = None,
) -> int:
    """Vide puis recharge linkage.grappes_identite avec l'affectation au
    SEUIL RETENU : une ligne par enregistrement de la population, y
    compris les singletons.
    """
    lignes = [
        (n_ipp, cluster_id, tailles[cluster_id], seuil) for n_ipp, cluster_id in affectation.items()
    ]
    with _connexion(environ) as connexion, connexion.cursor() as curseur:
        curseur.execute("truncate table linkage.grappes_identite")
        curseur.executemany(
            "insert into linkage.grappes_identite (n_ipp, grappe_id, taille_grappe, seuil) "
            "values (%s, %s, %s, %s)",
            lignes,
        )
        connexion.commit()
    return len(lignes)


def main() -> None:
    population = extraire_population()
    paires_vt = paires_verite_terrain_presentes(population)
    paires = paires_predites(population)

    ensemble_restreint: set[str] = set()
    for n1, n2 in paires_vt:
        ensemble_restreint.add(n1)
        ensemble_restreint.add(n2)

    poids_vt = [w for _n1, _n2, _p, w in paires if (_n1, _n2) in paires_vt]
    poids_non_vt = [w for _n1, _n2, _p, w in paires if (_n1, _n2) not in paires_vt]
    grille = sorted(
        set(grille_seuils_requise())
        | set(grille_seuils_etendue(max(poids_non_vt), min(poids_vt)))
        | set(grille_seuils_mode_bas(poids_non_vt))
    )

    lignes = balayage(paires, population, grille, paires_vt, ensemble_restreint)
    nb_eval = charger_evaluation(lignes)
    print(f"linkage.evaluation : {nb_eval} ligne(s) écrite(s)")

    chemin_csv = RACINE / "linkage" / "courbe_precision_rappel.csv"
    nb_csv = ecrire_courbe_csv(lignes, chemin_csv)
    print(f"{chemin_csv} : {nb_csv} ligne(s) écrite(s)")

    paires_pour_regroupement = [(n1, n2, proba) for n1, n2, proba, _poids in paires]
    affectation = composantes_connexes(paires_pour_regroupement, SEUIL_PROBABILITE, population)
    tailles = tailles_des_grappes(affectation)
    nb_grappes = charger_grappes_identite(affectation, tailles, SEUIL_PROBABILITE)
    print(f"linkage.grappes_identite : {nb_grappes} ligne(s) écrite(s)")


if __name__ == "__main__":
    main()
