"""Tests de l'évaluation : balayage, seuil retenu, tables peuplées.

Exige la base (tables déjà peuplées par `linkage.evaluation`, jamais
recalculées ici sauf pour la confrontation à la référence, une requête
légère). Aucun littéral de volumétrie.
"""

from linkage.evaluation import (
    SEUIL_PROBABILITE,
    baseline_paires,
    metriques_paire,
    paires_verite_terrain_presentes,
)
from linkage.population import _connexion, extraire_population


def test_chaque_ligne_verifie_vp_plus_fn_egale_denominateur():
    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "select vrais_positifs, faux_negatifs, nb_paires_verite_terrain from linkage.evaluation"
        )
        lignes = curseur.fetchall()
    assert lignes, "table linkage.evaluation vide : rien à vérifier"
    for vp, fn, denominateur in lignes:
        assert vp + fn == denominateur


def test_precision_rappel_f_mesure_coherents_avec_les_comptes():
    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "select vrais_positifs, faux_positifs, faux_negatifs, "
            "precision_valeur, rappel, f_mesure from linkage.evaluation"
        )
        lignes = curseur.fetchall()
    assert lignes
    for vp, fp, fn, precision, rappel, f_mesure in lignes:
        precision_attendue = vp / (vp + fp) if (vp + fp) else 0.0
        rappel_attendu = vp / (vp + fn) if (vp + fn) else 0.0
        f_mesure_attendue = (
            2 * precision_attendue * rappel_attendu / (precision_attendue + rappel_attendu)
            if (precision_attendue + rappel_attendu) > 0
            else 0.0
        )
        assert abs(precision - precision_attendue) < 1e-9
        assert abs(rappel - rappel_attendu) < 1e-9
        assert abs(f_mesure - f_mesure_attendue) < 1e-9


def test_table_grappes_couvre_exactement_la_population():
    population = extraire_population()
    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute("select count(*) from linkage.grappes_identite")
        (nb_lignes,) = curseur.fetchone()

    assert nb_lignes == len(population)

    # la somme des tailles distinctes (une grappe comptée une fois, pas une
    # fois par enregistrement) doit égaler le nombre d'enregistrements
    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute("select distinct grappe_id, taille_grappe from linkage.grappes_identite")
        tailles_distinctes = curseur.fetchall()
    somme_tailles = sum(taille for _grappe_id, taille in tailles_distinctes)
    assert somme_tailles == len(population)


def test_grappes_taille_deux_egale_paires_verite_terrain_au_seuil_retenu():
    population = extraire_population()
    paires_vt = paires_verite_terrain_presentes(population)

    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "select count(*) from ("
            "  select grappe_id from linkage.grappes_identite"
            "  where seuil = %s group by grappe_id having count(*) = 2"
            ") t",
            [SEUIL_PROBABILITE],
        )
        (nb_grappes_taille2,) = curseur.fetchone()

    assert nb_grappes_taille2 == len(paires_vt)


def test_f_mesure_au_seuil_retenu_au_moins_egale_a_la_reference():
    population = extraire_population()
    paires_vt = paires_verite_terrain_presentes(population)
    baseline = baseline_paires()
    paires_baseline_avec_score = [(n1, n2, 1.0, 0.0) for n1, n2 in baseline["union"]]
    metriques_baseline = metriques_paire(paires_baseline_avec_score, 0.5, paires_vt)

    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "select f_mesure from linkage.evaluation where seuil = %s", [SEUIL_PROBABILITE]
        )
        (f_mesure_modele,) = curseur.fetchone()

    assert f_mesure_modele >= metriques_baseline["f_mesure"]
