"""Applique les fichiers .sql de linkage/ddl/ à PostgreSQL, dans l'ordre alphabétique.

ingestion/appliquer_ddl.py vise un répertoire fixe (ingestion/ddl/, sans
paramètre de répertoire) : il ne peut pas être réutilisé tel quel pour
linkage/ddl/ sans le modifier, ce qui est hors de portée de ce module. Cet
applicateur minimal réutilise donc, par import, le découpage d'instructions
SQL de ingestion.appliquer_ddl (`diviser_instructions`, qui gère les
littéraux entre apostrophes et les commentaires de ligne) et la résolution
des paramètres de connexion déjà écrite dans linkage.population
(`parametres_connexion`), plutôt que de dupliquer l'une ou l'autre.
"""

import sys
from pathlib import Path

import psycopg

from ingestion.appliquer_ddl import diviser_instructions
from linkage.population import ParametreConnexionManquant, parametres_connexion

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DDL = RACINE / "linkage" / "ddl"


def main() -> None:
    try:
        p = parametres_connexion()
    except ParametreConnexionManquant as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    fichiers = sorted(DOSSIER_DDL.glob("*.sql"))

    with (
        psycopg.connect(
            host=p["POSTGRES_HOST"],
            port=p["POSTGRES_PORT"],
            dbname=p["POSTGRES_DB"],
            user=p["POSTGRES_USER"],
            password=p["POSTGRES_PASSWORD"],
            autocommit=True,
        ) as connexion,
        connexion.cursor() as curseur,
    ):
        for fichier in fichiers:
            instructions = diviser_instructions(fichier.read_text(encoding="utf-8"))
            for instruction in instructions:
                curseur.execute(instruction)
            print(f"{fichier.name}: {len(instructions)} instruction(s)")


if __name__ == "__main__":
    main()
