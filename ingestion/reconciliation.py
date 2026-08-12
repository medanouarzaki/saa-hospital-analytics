"""Réconcilie le contenu de la base contre le manifeste du générateur.

Lit un fichier de manifeste (chemin en argument) comme un fichier de données YAML — jamais
via le code qui l'a produit, `generator/` reste hors de portée de ce module — interroge
`source` et `quarantaine` pour chaque table, et compare le décompte du manifeste à la somme
des deux. Aucun décompte attendu n'est écrit dans ce script : il mesure et compare, il ne
connaît aucun chiffre d'avance.
"""

import argparse
import sys
from pathlib import Path

import yaml

from ingestion import chargeur


def charger_manifeste(chemin: Path) -> dict:
    with chemin.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def decomptes_base(table: str) -> tuple[int, int]:
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(f"select count(*) from source.{table}")
        n_source = cur.fetchone()[0]
        cur.execute(f"select count(*) from quarantaine.{table}")
        n_quarantaine = cur.fetchone()[0]
    return n_source, n_quarantaine


def ventilation_quarantaine(table: str) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    """Décompte par motif (premier segment avant `:`) et par (table, colonne) pour les
    motifs qui en portent une (deuxième segment)."""
    par_motif: dict[str, int] = {}
    par_colonne: dict[tuple[str, str], int] = {}
    with chargeur.connexion() as conn, conn.cursor() as cur:
        cur.execute(f"select rejet_motifs from quarantaine.{table}")
        lignes = cur.fetchall()
    for (motifs_joints,) in lignes:
        for motif in motifs_joints.split(";"):
            segments = motif.split(":")
            nom_motif = segments[0]
            par_motif[nom_motif] = par_motif.get(nom_motif, 0) + 1
            if len(segments) >= 2:
                cle = (table, segments[1])
                par_colonne[cle] = par_colonne.get(cle, 0) + 1
    return par_motif, par_colonne


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Réconcilie source+quarantaine contre le manifeste du générateur."
    )
    analyseur.add_argument("manifeste", type=Path, help="Chemin du fichier manifeste.yml")
    arguments = analyseur.parse_args(argv)

    manifeste = charger_manifeste(arguments.manifeste)
    decompte_manifeste = manifeste["decompte_lignes"]

    toutes_egalites = True
    print("=== Réconciliation par table ===")
    for table_qualifiee in sorted(decompte_manifeste):
        table = table_qualifiee.removeprefix("source.")
        attendu = decompte_manifeste[table_qualifiee]
        n_source, n_quarantaine = decomptes_base(table)
        somme = n_source + n_quarantaine
        egalite = somme == attendu
        toutes_egalites = toutes_egalites and egalite
        print(
            f"{table_qualifiee}: manifeste={attendu} source={n_source} "
            f"quarantaine={n_quarantaine} somme={somme} egalite={egalite}"
        )

    print()
    print("=== Ventilation de la quarantaine ===")
    for table_qualifiee in sorted(decompte_manifeste):
        table = table_qualifiee.removeprefix("source.")
        par_motif, par_colonne = ventilation_quarantaine(table)
        if not par_motif:
            continue
        print(f"-- {table_qualifiee} --")
        print(f"  par motif: {dict(sorted(par_motif.items()))}")
        for (t, colonne), n in sorted(par_colonne.items()):
            print(f"  par colonne: {t}.{colonne} = {n}")

    return 0 if toutes_egalites else 1


if __name__ == "__main__":
    sys.exit(main())
