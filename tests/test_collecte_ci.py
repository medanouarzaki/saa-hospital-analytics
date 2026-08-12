"""Contrôle que la matrice de jobs de tests dans `.github/workflows/ci.yml` couvre
exactement les fichiers de test présents sur le disque, dans les deux sens.

Un fichier de test ajouté sans être placé dans un groupe de la matrice ne serait jamais
exécuté en intégration continue sans qu'aucun échec ne le signale ; un nom de fichier
fantôme dans un groupe échouerait silencieusement au niveau de pytest (`ERROR: file not
found`) sans qu'on remonte facilement à la cause. Ce test relie les deux : l'union des
fichiers de tous les groupes de la matrice, plus `tests/test_provenance.py` (exécuté par un
job séparé, hors matrice), doit égaler exactement l'ensemble des `tests/test_*.py`
présents.
"""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
CI = RACINE / ".github" / "workflows" / "ci.yml"
PROVENANCE = "tests/test_provenance.py"


def _fichiers_de_la_matrice() -> set[str]:
    contenu = yaml.safe_load(CI.read_text(encoding="utf-8"))
    groupes = contenu["jobs"]["tests-matrice"]["strategy"]["matrix"]["groupe"]
    fichiers: set[str] = set()
    for groupe in groupes:
        fichiers.update(groupe["fichiers"].split())
    return fichiers


def _fichiers_sur_disque() -> set[str]:
    return {f"tests/{p.name}" for p in RACINE.glob("tests/test_*.py")}


def test_matrice_couvre_exactement_les_fichiers_de_test_sur_disque() -> None:
    fichiers_matrice = _fichiers_de_la_matrice()
    fichiers_disque = _fichiers_sur_disque()

    fichiers_matrice_et_provenance = fichiers_matrice | {PROVENANCE}

    manquants = fichiers_disque - fichiers_matrice_et_provenance
    fantomes = fichiers_matrice_et_provenance - fichiers_disque

    assert not manquants, (
        f"fichiers de test présents sur le disque mais absents de la matrice CI et du job "
        f"provenance : {sorted(manquants)}"
    )
    assert not fantomes, (
        f"fichiers référencés par la matrice CI ou le job provenance mais absents du "
        f"disque : {sorted(fantomes)}"
    )


def test_aucun_fichier_reparti_dans_plus_d_un_groupe() -> None:
    contenu = yaml.safe_load(CI.read_text(encoding="utf-8"))
    groupes = contenu["jobs"]["tests-matrice"]["strategy"]["matrix"]["groupe"]

    vus: dict[str, str] = {}
    doublons: list[str] = []
    for groupe in groupes:
        for fichier in groupe["fichiers"].split():
            if fichier in vus:
                doublons.append(f"{fichier} (groupes {vus[fichier]!r} et {groupe['nom']!r})")
            else:
                vus[fichier] = groupe["nom"]

    assert not doublons, f"fichiers présents dans plus d'un groupe de la matrice : {doublons}"
