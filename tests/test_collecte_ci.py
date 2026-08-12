"""Contrôle que la CI, lue dans `.github/workflows/ci.yml`, couvre exactement les fichiers
de test présents sur le disque, dans les deux sens, et qu'aucun fichier n'apparaît dans plus
d'un emplacement.

Deux emplacements où un fichier de test peut être exécuté : un groupe de la matrice
`tests-matrice`, ou la commande pytest du job `provenance`. Un fichier de test ajouté sans
être placé dans l'un des deux ne serait jamais exécuté en intégration continue sans qu'aucun
échec ne le signale ; un nom de fichier fantôme échouerait silencieusement au niveau de
pytest (`ERROR: file not found`) sans qu'on remonte facilement à la cause ; un fichier placé
dans les deux emplacements s'exécuterait deux fois sans que rien ne le signale non plus. Ce
test relie les trois propriétés : l'union des deux emplacements égale exactement l'ensemble
des `tests/test_*.py` présents, et les deux emplacements sont disjoints.

Les fichiers du job `provenance` ne sont pas une constante : ils sont extraits de la
commande pytest de ce job, lue dans `ci.yml`, par le même principe que les groupes de la
matrice — la liste vient du fichier de configuration, jamais d'un nom recopié à la main qui
pourrait diverger silencieusement de la commande réellement exécutée.
"""

import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
CI = RACINE / ".github" / "workflows" / "ci.yml"

MOTIF_FICHIER_TEST = re.compile(r"tests/\S+\.py")


def _fichiers_de_la_matrice() -> set[str]:
    contenu = yaml.safe_load(CI.read_text(encoding="utf-8"))
    groupes = contenu["jobs"]["tests-matrice"]["strategy"]["matrix"]["groupe"]
    fichiers: set[str] = set()
    for groupe in groupes:
        fichiers.update(groupe["fichiers"].split())
    return fichiers


def _fichiers_du_job_provenance() -> set[str]:
    contenu = yaml.safe_load(CI.read_text(encoding="utf-8"))
    etapes = contenu["jobs"]["provenance"]["steps"]

    fichiers: set[str] = set()
    for etape in etapes:
        commande = etape.get("run", "")
        if "pytest" not in commande:
            continue
        fichiers.update(MOTIF_FICHIER_TEST.findall(commande))
    return fichiers


def _fichiers_par_emplacement() -> dict[str, set[str]]:
    return {
        "matrice": _fichiers_de_la_matrice(),
        "provenance": _fichiers_du_job_provenance(),
    }


def _fichiers_sur_disque() -> set[str]:
    return {f"tests/{p.name}" for p in RACINE.glob("tests/test_*.py")}


def test_ci_couvre_exactement_les_fichiers_de_test_sur_disque() -> None:
    emplacements = _fichiers_par_emplacement()
    fichiers_ci: set[str] = set().union(*emplacements.values())
    fichiers_disque = _fichiers_sur_disque()

    manquants = fichiers_disque - fichiers_ci
    fantomes = fichiers_ci - fichiers_disque

    assert not manquants, (
        f"fichiers de test présents sur le disque mais absents de la CI (matrice et job "
        f"provenance) : {sorted(manquants)}"
    )
    assert not fantomes, (
        f"fichiers référencés par la CI (matrice ou job provenance) mais absents du "
        f"disque : {sorted(fantomes)}"
    )


def test_aucun_fichier_reparti_dans_plus_d_un_emplacement() -> None:
    emplacements = _fichiers_par_emplacement()

    vus: dict[str, str] = {}
    doublons: list[str] = []
    for nom_emplacement, fichiers in emplacements.items():
        for fichier in fichiers:
            if fichier in vus:
                doublons.append(f"{fichier} (emplacements {vus[fichier]!r} et {nom_emplacement!r})")
            else:
                vus[fichier] = nom_emplacement

    assert not doublons, f"fichiers présents dans plus d'un emplacement de la CI : {doublons}"
