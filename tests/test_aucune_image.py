"""Interdit toute image du système d'information dans les fichiers suivis."""

import subprocess
from pathlib import Path, PurePosixPath

RACINE = Path(__file__).resolve().parent.parent
EXTENSIONS_INTERDITES = {".heic", ".jpg", ".jpeg", ".png"}

# Bloc 9 : les captures du tableau de bord produit par le projet seront tolérées
# sous ce préfixe et nulle part ailleurs. Vide jusque-là.
PREFIXES_TOLERES: tuple[str, ...] = ()


def fichiers_suivis() -> list[str]:
    sortie = subprocess.run(
        ["git", "-C", str(RACINE), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [chemin for chemin in sortie.split("\0") if chemin]


def dans_le_perimetre(chemin: str) -> bool:
    parties = PurePosixPath(chemin).parts
    return len(parties) == 1 or parties[0] == "report"


def test_aucune_image_du_systeme() -> None:
    fautifs = sorted(
        chemin
        for chemin in fichiers_suivis()
        if dans_le_perimetre(chemin)
        and PurePosixPath(chemin).suffix.lower() in EXTENSIONS_INTERDITES
        and not chemin.startswith(PREFIXES_TOLERES)
    )
    assert not fautifs, "Fichiers image suivis interdits : " + ", ".join(fautifs)
