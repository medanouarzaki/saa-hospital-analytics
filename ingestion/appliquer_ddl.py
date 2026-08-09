"""Applique les fichiers .sql de ingestion/ddl/ à PostgreSQL, dans l'ordre alphabétique.

Les paramètres de connexion viennent de l'environnement du processus ; un
fichier .env à la racine, s'il existe, ne fait que compléter les variables
absentes, il ne prend jamais le pas sur l'environnement du processus. C'est
ce qui permet à la même logique de servir localement, avec .env, et en
intégration continue, où seules les variables d'environnement du job
existent. Aucune valeur de connexion n'est jamais imprimée.
"""

import os
import sys
from pathlib import Path

import psycopg

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DDL = RACINE / "ingestion" / "ddl"
FICHIER_ENV = RACINE / ".env"

CLES_CONNEXION = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
]


def charger_environnement() -> dict[str, str]:
    variables = dict(os.environ)
    if FICHIER_ENV.exists():
        for ligne in FICHIER_ENV.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, _, valeur = ligne.partition("=")
            variables.setdefault(cle.strip(), valeur.strip())
    return variables


def diviser_instructions(sql: str) -> list[str]:
    """Découpe un script en instructions, en respectant les littéraux entre
    apostrophes et les commentaires de ligne, où une apostrophe ne délimite
    rien.
    """
    instructions = []
    courant: list[str] = []
    dans_chaine = False
    dans_commentaire = False
    i = 0
    n = len(sql)
    while i < n:
        caractere = sql[i]
        courant.append(caractere)
        if dans_commentaire:
            if caractere == "\n":
                dans_commentaire = False
        elif dans_chaine:
            if caractere == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    courant.append(sql[i + 1])
                    i += 1
                else:
                    dans_chaine = False
        elif caractere == "-" and i + 1 < n and sql[i + 1] == "-":
            dans_commentaire = True
            courant.append(sql[i + 1])
            i += 1
        elif caractere == "'":
            dans_chaine = True
        elif caractere == ";":
            instructions.append("".join(courant))
            courant = []
        i += 1
    reste = "".join(courant).strip()
    if reste:
        instructions.append(reste)
    return [instr for instr in instructions if not est_vide(instr)]


def est_vide(instruction: str) -> bool:
    lignes = (ligne.strip() for ligne in instruction.splitlines())
    lignes_utiles = [ligne for ligne in lignes if ligne and not ligne.startswith("--")]
    return not lignes_utiles


def main() -> None:
    variables = charger_environnement()
    manquantes = [cle for cle in CLES_CONNEXION if not variables.get(cle)]
    if manquantes:
        print(f"variables de connexion manquantes : {', '.join(manquantes)}", file=sys.stderr)
        raise SystemExit(1)

    conninfo = {
        "host": variables["POSTGRES_HOST"],
        "port": variables["POSTGRES_PORT"],
        "dbname": variables["POSTGRES_DB"],
        "user": variables["POSTGRES_USER"],
        "password": variables["POSTGRES_PASSWORD"],
    }

    fichiers = sorted(DOSSIER_DDL.glob("*.sql"))

    with psycopg.connect(**conninfo, autocommit=True) as connexion, connexion.cursor() as curseur:
        for fichier in fichiers:
            instructions = diviser_instructions(fichier.read_text(encoding="utf-8"))
            for instruction in instructions:
                curseur.execute(instruction)
            print(f"{fichier.name}: {len(instructions)} instruction(s)")


if __name__ == "__main__":
    main()
