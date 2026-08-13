"""Contrôles bloquants sur le point d'entrée en ligne de commande (generator/__main__.py)."""

import subprocess
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent


def test_aide_fonctionne() -> None:
    resultat = subprocess.run(
        [sys.executable, "-m", "generator", "--help"],
        cwd=RACINE,
        capture_output=True,
        text=True,
    )
    assert resultat.returncode == 0
    assert "racine" in resultat.stdout
    assert "--date-debut" in resultat.stdout
    assert "--date-fin" in resultat.stdout


def test_cli_honore_la_periode_demandee(tmp_path: Path) -> None:
    date_debut = "2024-01-01"
    date_fin = "2024-01-31"
    resultat = subprocess.run(
        [
            sys.executable,
            "-m",
            "generator",
            str(tmp_path),
            "--graine",
            "7",
            "--date-debut",
            date_debut,
            "--date-fin",
            date_fin,
        ],
        cwd=RACINE,
        capture_output=True,
        text=True,
    )
    assert resultat.returncode == 0, resultat.stderr

    with (tmp_path / "manifeste.yml").open(encoding="utf-8") as f:
        manifeste = yaml.safe_load(f)

    assert manifeste["periode"]["debut"] == date_debut
    assert manifeste["periode"]["fin"] == date_fin
    assert manifeste["graine"] == 7

    # aucune partition en dehors de la periode demandee, sur toutes les tables
    for chemins in manifeste["partitions"].values():
        for relatif in chemins:
            date_partition = relatif.split("/")[2]
            assert date_debut <= date_partition <= date_fin, relatif
