"""Rejoue les commandes du registre des chiffres et confronte leurs valeurs aux valeurs consignées.

DEUX MODES, ET LA DIFFÉRENCE EST LE POINT DE CONCEPTION DE CET OUTIL.

`--verifier` rejoue tout le registre sur la base COMPLÈTE et diffe les valeurs obtenues contre les
valeurs consignées. C'est la commande qui PROUVE les nombres du rapport, et elle est destinée à être
rejouée avant la remise. Elle ne peut s'exécuter que là où la période entière est chargée.

`--formes` exécute les mêmes commandes sans comparer les valeurs, et vérifie seulement que chacune
s'exécute encore et rend une valeur du type attendu. C'est tout ce que l'intégration continue peut
prouver : elle génère une fenêtre de trois mois, où les valeurs de la période entière n'existent
pas. Une comparaison y rougirait toujours, et un contrôle rouge en permanence n'est plus un
contrôle.

Aucune valeur de connexion n'est imprimée. Aucune instruction de modification n'est émise : les
commandes du registre sont des lectures, et la propriété est vérifiée avant exécution.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

import psycopg
import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
REGISTRE = Path(__file__).resolve().parent / "registre_chiffres.yml"
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"

# Une commande du registre est une LECTURE. Le motif refuse tout ce qui n'ouvre pas sur `select`,
# et la garde est appliquée avant d'ouvrir la connexion.
_LECTURE = re.compile(r"^\s*select\b", re.IGNORECASE)

TYPES_ATTENDUS = {
    "lignes": int,
    "tables": int,
    "colonnes": int,
    "paramètres": int,
    "fichiers": int,
    "familles": int,
    "séjours": int,
    "consultations": int,
    "passages": int,
    "fiches": int,
    "personnes": int,
    "journées": int,
    "prélèvements": int,
    "examens": int,
    "interventions": int,
    "lits": int,
    "jours": int,
    "tranches": int,
    "niveaux": int,
    "factures": int,
    "partitions": int,
    "modèles": int,
    "dimensions": int,
    "faits": int,
    "agrégats": int,
    "identifiants": int,
    "grappes": int,
    "tâches": int,
    "versions": int,
    "%": float,
    "proportion": float,
    "jours (moyenne)": float,
    "passages/jour": int,
    "date": str,
}


def charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def connexion() -> psycopg.Connection:
    variables = charger_module(APPLIQUER_DDL).charger_environnement()
    return psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables.get("POSTGRES_PASSWORD", ""),
        connect_timeout=5,
    )


def charger_registre() -> dict:
    with REGISTRE.open(encoding="utf-8") as fichier:
        return yaml.safe_load(fichier)


def normaliser(valeur):
    """Un décimal exact rendu par le serveur se compare à un flottant du registre."""
    if isinstance(valeur, bool):
        return valeur
    if hasattr(valeur, "__float__") and not isinstance(valeur, (int, float, str)):
        return float(valeur)
    return valeur


def executer(entrees: list[dict], curseur) -> dict[str, object]:
    espace = {"yaml": yaml, "R": RACINE, "Path": Path}
    obtenues = {}
    for entree in entrees:
        if entree["type"] == "sql":
            curseur.execute(entree["commande"])
            obtenues[entree["id"]] = normaliser(curseur.fetchone()[0])
        else:
            obtenues[entree["id"]] = normaliser(eval(entree["commande"], espace))  # noqa: S307
    return obtenues


def refuser_les_ecritures(entrees: list[dict]) -> list[str]:
    return [e["id"] for e in entrees if e["type"] == "sql" and not _LECTURE.match(e["commande"])]


def main(arguments: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python docs/chiffres/mesurer.py",
        description=(
            "Rejoue les commandes du registre des chiffres. `--verifier` compare les valeurs "
            "obtenues aux valeurs consignées et n'a de sens que sur la période entière ; "
            "`--formes` vérifie seulement que chaque commande s'exécute et rend le type attendu."
        ),
    )
    groupe = analyseur.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--verifier", action="store_true", help="comparer les valeurs consignées")
    groupe.add_argument("--formes", action="store_true", help="n'exécuter que, sans comparer")
    options = analyseur.parse_args(arguments)

    registre = charger_registre()
    entrees = registre["chiffres"]

    ecritures = refuser_les_ecritures(entrees)
    if ecritures:
        print("commandes qui ne sont pas des lectures : " + ", ".join(ecritures))
        return 2

    with connexion() as conn, conn.cursor() as curseur:
        obtenues = executer(entrees, curseur)
        if options.verifier:
            ancrages = []
            for ancre in registre["ancrage"]:
                curseur.execute(ancre["commande"])
                obtenu = curseur.fetchone()[0]
                if obtenu != ancre["lignes"]:
                    ancrages.append(
                        f"{ancre['objet']} : consigné {ancre['lignes']}, obtenu {obtenu}"
                    )
            if ancrages:
                print("ANCRAGE ROMPU — les valeurs de portée")
                print("`periode-entiere` ne sont pas comparables :")
                for ligne in ancrages:
                    print(f"  {ligne}")
                return 3

    if options.formes:
        fautes = []
        for entree in entrees:
            attendu = TYPES_ATTENDUS.get(entree["unite"])
            obtenu = obtenues[entree["id"]]
            if attendu is None:
                fautes.append(f"{entree['id']} : unité « {entree['unite']} » sans type attendu")
            elif attendu is float and isinstance(obtenu, int):
                continue
            elif not isinstance(obtenu, attendu):
                fautes.append(
                    f"{entree['id']} : la commande rend {type(obtenu).__name__}, "
                    f"{attendu.__name__} attendu pour l'unité « {entree['unite']} »"
                )
        for ligne in fautes:
            print(ligne)
        print(f"{len(entrees)} commande(s) exécutée(s), {len(fautes)} de forme inattendue")
        return 1 if fautes else 0

    ecarts = []
    for entree in entrees:
        consignee, obtenue = normaliser(entree["valeur"]), obtenues[entree["id"]]
        if consignee != obtenue:
            ecarts.append(f"{entree['id']} : consigné {consignee}, mesuré {obtenue}")
    for ligne in ecarts:
        print(ligne)
    print(f"{len(entrees)} entrée(s) confrontée(s), {len(ecarts)} écart(s)")
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main())
