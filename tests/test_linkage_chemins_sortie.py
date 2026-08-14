"""Chemins de sortie paramétrables de linkage.evaluation et linkage.ablation.

Deux propriétés, sur les deux modules : la valeur par défaut (variable d'environnement
absente) reste le chemin actuel du dépôt — jamais recopiée en chaîne littérale, toujours
recomposée depuis la racine du dépôt — et la variable, quand elle est définie, est honorée.
N'importe aucun autre symbole de ces deux modules : ce fichier ne porte que sur leurs chemins
de sortie.
"""

import importlib
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def test_ablation_chemin_par_defaut() -> None:
    import linkage.ablation as ablation

    importlib.reload(ablation)
    assert ablation.CHEMIN_CSV == RACINE / "linkage" / "ablation.csv"


def test_evaluation_chemin_par_defaut() -> None:
    import linkage.evaluation as evaluation

    importlib.reload(evaluation)
    assert evaluation.CHEMIN_COURBE == RACINE / "linkage" / "courbe_precision_rappel.csv"


def test_ablation_variable_environnement_honoree(tmp_path) -> None:
    import linkage.ablation as ablation

    cible = tmp_path / "ablation_redirige.csv"
    os.environ["CHEMIN_CSV_ABLATION"] = str(cible)
    try:
        importlib.reload(ablation)
        assert cible == ablation.CHEMIN_CSV
    finally:
        del os.environ["CHEMIN_CSV_ABLATION"]
        importlib.reload(ablation)


def test_evaluation_variable_environnement_honoree(tmp_path) -> None:
    import linkage.evaluation as evaluation

    cible = tmp_path / "courbe_redirigee.csv"
    os.environ["CHEMIN_COURBE_PRECISION_RAPPEL"] = str(cible)
    try:
        importlib.reload(evaluation)
        assert cible == evaluation.CHEMIN_COURBE
    finally:
        del os.environ["CHEMIN_COURBE_PRECISION_RAPPEL"]
        importlib.reload(evaluation)
