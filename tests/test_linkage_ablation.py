"""Tests de l'étude d'ablation (linkage.ablation).

Ne réestime JAMAIS les modèles (coûteux, quatre sessions EM complètes) :
lit uniquement le fichier versionné déjà écrit par `python -m
linkage.ablation` (linkage/ablation.csv) et le compare à la table
linkage.evaluation, déjà peuplée par `python -m linkage.evaluation` — deux
sources calculées indépendamment, dont l'égalité au seuil retenu est la
propriété vérifiée ici. Aucun littéral de volumétrie : chaque grandeur
comparée est lue, jamais recopiée en dur.
"""

import csv
from pathlib import Path

import pytest

from linkage.ablation import VARIANTES
from linkage.evaluation import SEUIL_PROBABILITE
from linkage.population import _connexion

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_CSV = RACINE / "linkage" / "ablation.csv"


@pytest.fixture(scope="module")
def lignes_ablation() -> list[dict]:
    with CHEMIN_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_une_ligne_par_variante(lignes_ablation):
    noms_csv = {ligne["variante"] for ligne in lignes_ablation}
    assert noms_csv == set(VARIANTES.keys())
    assert len(lignes_ablation) == len(VARIANTES)


def test_compte_de_paires_candidates_identique_sur_les_quatre_variantes(lignes_ablation):
    comptes = {int(ligne["nb_paires_candidates"]) for ligne in lignes_ablation}
    assert len(comptes) == 1, (
        f"le blocage est censé être identique sur toutes les variantes : {comptes}"
    )


def test_ligne_complete_correspond_a_linkage_evaluation_au_seuil_retenu(lignes_ablation):
    """La ligne 'complet' de linkage/ablation.csv (calculée par une
    réestimation indépendante dans linkage.ablation) doit égaler ce que
    linkage.evaluation a écrit dans la table, au seuil retenu — deux
    sources de calcul indépendantes, la même vérité.
    """
    ligne_complete = next(ligne for ligne in lignes_ablation if ligne["variante"] == "complet")

    with _connexion() as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "select vrais_positifs, faux_positifs, faux_negatifs, "
            "precision_valeur, rappel, f_mesure, "
            "nb_grappes_exactes_restreint, nb_grappes_exactes_global, "
            "nb_enregistrements_sur_fusionnes_restreint, nb_enregistrements_sur_fusionnes_global "
            "from linkage.evaluation where seuil = %s",
            [SEUIL_PROBABILITE],
        )
        ligne_table = curseur.fetchone()
    assert ligne_table is not None, "aucune ligne linkage.evaluation au seuil retenu"
    (
        vp_table,
        fp_table,
        fn_table,
        precision_table,
        rappel_table,
        f_mesure_table,
        grappe_restreint_table,
        grappe_global_table,
        sur_fus_restreint_table,
        sur_fus_global_table,
    ) = ligne_table

    assert int(ligne_complete["vrais_positifs"]) == vp_table
    assert int(ligne_complete["faux_positifs"]) == fp_table
    assert int(ligne_complete["faux_negatifs"]) == fn_table
    assert abs(float(ligne_complete["precision"]) - precision_table) < 1e-9
    assert abs(float(ligne_complete["rappel"]) - rappel_table) < 1e-9
    assert abs(float(ligne_complete["f_mesure"]) - f_mesure_table) < 1e-9
    assert int(ligne_complete["grappe_restreint_vraies_retrouvees"]) == grappe_restreint_table
    assert int(ligne_complete["grappe_global_vraies_retrouvees"]) == grappe_global_table
    assert int(ligne_complete["grappe_restreint_sur_fusionnes"]) == sur_fus_restreint_table
    assert int(ligne_complete["grappe_global_sur_fusionnes"]) == sur_fus_global_table


def test_ecart_negatif_signale_un_chevauchement(lignes_ablation):
    """Propriété structurelle : une variante dont la marge (poids_min_vt -
    poids_max_non_vt) est négative a, par construction, des paires
    non-vraies au-dessus de paires vraies dans l'espace des poids — un
    chevauchement des deux distributions.
    """
    for ligne in lignes_ablation:
        ecart = float(ligne["ecart"])
        poids_max_non_vt = float(ligne["poids_max_non_vt"])
        poids_min_vt = float(ligne["poids_min_vt"])
        assert abs(ecart - (poids_min_vt - poids_max_non_vt)) < 1e-6
        if ecart < 0:
            assert poids_max_non_vt > poids_min_vt


def test_f_mesure_au_seuil_retenu_coherente_avec_les_comptes(lignes_ablation):
    for ligne in lignes_ablation:
        vp = int(ligne["vrais_positifs"])
        fp = int(ligne["faux_positifs"])
        fn = int(ligne["faux_negatifs"])
        precision_attendue = vp / (vp + fp) if (vp + fp) else 0.0
        rappel_attendu = vp / (vp + fn) if (vp + fn) else 0.0
        f_mesure_attendue = (
            2 * precision_attendue * rappel_attendu / (precision_attendue + rappel_attendu)
            if (precision_attendue + rappel_attendu) > 0
            else 0.0
        )
        assert abs(float(ligne["precision"]) - precision_attendue) < 1e-9
        assert abs(float(ligne["rappel"]) - rappel_attendu) < 1e-9
        assert abs(float(ligne["f_mesure"]) - f_mesure_attendue) < 1e-9


def test_depasse_la_baseline_coherent_avec_les_deux_f_mesures(lignes_ablation):
    for ligne in lignes_ablation:
        f_mesure = float(ligne["f_mesure"])
        baseline = float(ligne["f_mesure_baseline_collision_exacte"])
        depasse = ligne["depasse_la_baseline"] == "True"
        assert depasse == (f_mesure >= baseline)
