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

LES SÉRIES SUIVENT LA MÊME RÈGLE, ET ELLES SONT LE MOTIF DE CE QUI SUIT. Un graphique ou un tableau
dont les données seraient tapées dans la source de composition serait exactement ce que ce registre
existe pour empêcher : un nombre que plus rien ne rattache à une mesure. Une série est donc, comme
un scalaire, une commande — mais son résultat est un FICHIER DE DONNÉES que la composition lit. Le
registre porte l'empreinte de ce fichier, et deux liens la chaînent de bout en bout :

    commande  ==(--verifier)==>  empreinte du registre  ==(le contrôle du registre)==>  fichier lu

Aucun des deux liens n'est vérifié par le code qui vérifie l'autre. Retoucher un fichier de données
à la main rompt le second ; modifier une valeur du registre sans toucher à sa commande rompt le
premier. `--ecrire-series` est le SEUL chemin d'écriture de ces fichiers, et il n'écrit que ce que
les commandes rendent.

Aucune valeur de connexion n'est imprimée. Aucune instruction de modification n'est émise : les
commandes du registre sont des lectures, et la propriété est vérifiée avant exécution.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import psycopg
import yaml

RACINE = Path(__file__).resolve().parent.parent.parent
REGISTRE = Path(__file__).resolve().parent / "registre_chiffres.yml"
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"
# Les fichiers de données des séries siègent sous `report/`, à côté de ce qui les lit. Le chemin
# consigné au registre est relatif à ce répertoire, comme l'argument que `\addplot table` reçoit.
RACINE_SERIES = RACINE / "report"

# Une commande du registre est une LECTURE. Deux conditions, et non plus une seule : la commande
# ouvre sur `select` ou sur `with` — les séries ont des expressions de table communes, et refuser
# `with` les aurait toutes écartées — ET elle ne porte aucun mot-clé de modification. La seconde
# condition est celle qui compte depuis que `with` est admis : `with x as (delete ... returning)`
# ouvre bien sur `with` et écrit. La garde est appliquée avant d'ouvrir la connexion.
_LECTURE = re.compile(r"^\s*(?:select|with)\b", re.IGNORECASE)
_MODIFICATION = re.compile(
    r"\b(?:insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|merge)\b",
    re.IGNORECASE,
)

TYPES_ATTENDUS = {
    "lignes": int,
    "chapitres": int,
    "sections": int,
    "relations": int,
    "conclusions": int,
    "limites": int,
    "sources": int,
    "tables": int,
    "pages": int,
    "indicateurs": int,
    "graphiques": int,
    "lectures": int,
    "rubriques": int,
    "octets": int,
    "secondes": float,
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
    "points": int,
    "paires": int,
    "groupes": int,
    "comparaisons": int,
    "poids": float,
    "probabilité": float,
    "partitions": int,
    "modèles": int,
    "dimensions": int,
    "faits": int,
    "agrégats": int,
    "identifiants": int,
    "grappes": int,
    "heures": int,
    "minutes": int,
    "rendez-vous": int,
    "activités": int,
    "créances": int,
    "relances": int,
    "corrélation": float,
    "dirhams": float,
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


# Les deux séparateurs de colonnes admis, nommés plutôt qu'écrits. La virgule est celle de toutes
# les séries de mesures ; la tabulation existe pour les séries dont les cellules sont du TEXTE, où
# une virgule et un point-virgule se rencontrent tous deux à l'intérieur d'une cellule. Le nom est
# déclaré au registre, lu par le rendu et par le contrôle, et repris en clair dans la source de
# composition — trois endroits, une seule décision.
SEPARATEURS = {"virgule": ",", "tabulation": "\t"}


def separateur_de(serie: dict) -> str:
    return SEPARATEURS[serie.get("separateur", "virgule")]


def rendre_serie(colonnes: list[str], lignes: list[tuple], separateur: str = ",") -> str:
    """Le texte EXACT du fichier de données. Une seule fonction le produit, et c'est elle dont
    l'empreinte fait foi : le rendu ne peut donc pas diverger entre l'écriture et la vérification.
    """
    sortie = [separateur.join(colonnes)]
    sortie.extend(separateur.join(str(valeur) for valeur in ligne) for ligne in lignes)
    return "\n".join(sortie) + "\n"


def empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def executer_series(series: list[dict], curseur) -> dict[str, tuple[list[str], list[tuple]]]:
    """Les deux types de commande, comme pour les scalaires — l'asymétrie n'avait pas de motif.

    UNE COMMANDE `sql` NOMME SES COLONNES, UNE COMMANDE `python` NE LE PEUT PAS. La première rend
    des noms de colonnes que le serveur porte, et le registre les confronte à ce qu'il déclare ;
    la seconde rend une liste de lignes, et les colonnes viennent alors de la déclaration seule.
    Ce que `--formes` peut prouver diffère donc selon le type, et le dire ici évite de croire que
    les deux sont contrôlés pareil : sur une série `python`, c'est la LARGEUR de chaque ligne qui
    est confrontée au nombre de colonnes déclarées, faute de noms à comparer.
    """
    espace = {"yaml": yaml, "R": RACINE, "Path": Path}
    obtenues = {}
    for serie in series:
        if serie["type"] == "sql":
            curseur.execute(serie["commande"])
            lignes = curseur.fetchall()
            colonnes = [description.name for description in curseur.description]
        else:
            lignes = [tuple(ligne) for ligne in eval(serie["commande"], espace)]  # noqa: S307
            colonnes = list(serie["colonnes"])
        obtenues[serie["id"]] = (colonnes, lignes)
    return obtenues


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
    return [
        e["id"]
        for e in entrees
        if e["type"] == "sql"
        and (not _LECTURE.match(e["commande"]) or _MODIFICATION.search(e["commande"]))
    ]


def main(arguments: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python docs/chiffres/mesurer.py",
        description=(
            "Rejoue les commandes du registre des chiffres. `--verifier` compare les valeurs "
            "obtenues aux valeurs consignées et n'a de sens que sur la période entière ; "
            "`--formes` vérifie seulement que chaque commande s'exécute et rend le type attendu ; "
            "`--ecrire-series` réécrit les fichiers de données des séries, et il est le seul "
            "chemin par lequel ces fichiers s'écrivent."
        ),
    )
    groupe = analyseur.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--verifier", action="store_true", help="comparer les valeurs consignées")
    groupe.add_argument("--formes", action="store_true", help="n'exécuter que, sans comparer")
    groupe.add_argument(
        "--ecrire-series", action="store_true", help="réécrire les fichiers de données des séries"
    )
    options = analyseur.parse_args(arguments)

    registre = charger_registre()
    entrees = registre["chiffres"]
    series = registre.get("series", [])

    ecritures = refuser_les_ecritures(entrees) + refuser_les_ecritures(series)
    if ecritures:
        print("commandes qui ne sont pas des lectures : " + ", ".join(ecritures))
        return 2

    with connexion() as conn, conn.cursor() as curseur:
        obtenues = executer(entrees, curseur)
        series_obtenues = executer_series(series, curseur)
        if options.ecrire_series:
            for serie in series:
                colonnes, lignes = series_obtenues[serie["id"]]
                cible = RACINE_SERIES / serie["fichier"]
                cible.parent.mkdir(parents=True, exist_ok=True)
                texte = rendre_serie(colonnes, lignes, separateur_de(serie))
                cible.write_text(texte, encoding="utf-8")
                print(f"{serie['id']} : {len(lignes)} ligne(s), empreinte {empreinte(texte)}")
            return 0
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
        for serie in series:
            colonnes, lignes = series_obtenues[serie["id"]]
            attendues = list(serie["colonnes"])
            if colonnes != attendues:
                fautes.append(
                    f"{serie['id']} : la commande rend les colonnes {colonnes}, "
                    f"{attendues} déclarées au registre"
                )
            elif not lignes:
                fautes.append(f"{serie['id']} : la commande ne rend aucune ligne")
            else:
                largeurs = {len(ligne) for ligne in lignes}
                if largeurs != {len(attendues)}:
                    fautes.append(
                        f"{serie['id']} : lignes de largeur {sorted(largeurs)}, "
                        f"{len(attendues)} colonne(s) déclarée(s)"
                    )
        for ligne in fautes:
            print(ligne)
        print(
            f"{len(entrees)} commande(s) et {len(series)} série(s) exécutée(s), "
            f"{len(fautes)} de forme inattendue"
        )
        return 1 if fautes else 0

    ecarts = []
    for entree in entrees:
        consignee, obtenue = normaliser(entree["valeur"]), obtenues[entree["id"]]
        if consignee != obtenue:
            ecarts.append(f"{entree['id']} : consigné {consignee}, mesuré {obtenue}")
    for serie in series:
        colonnes, lignes = series_obtenues[serie["id"]]
        obtenue = empreinte(rendre_serie(colonnes, lignes, separateur_de(serie)))
        if obtenue != serie["empreinte"]:
            ecarts.append(
                f"{serie['id']} : le fichier que la commande produit a pour empreinte {obtenue}, "
                f"le registre consigne {serie['empreinte']} — la commande et le registre divergent"
            )
    for ligne in ecarts:
        print(ligne)
    print(
        f"{len(entrees)} entrée(s) et {len(series)} série(s) confrontée(s), {len(ecarts)} écart(s)"
    )
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main())
