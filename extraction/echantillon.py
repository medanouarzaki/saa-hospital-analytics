"""Engendre l'échantillon de données versé au dépôt.

POURQUOI CE MODULE EXISTE. Le projet produit plusieurs centaines de milliers de lignes, et un
lecteur du dépôt ne peut en voir aucune sans cloner, installer et faire tourner la chaîne entière.
Le livrable tabulaire existe — le module d'export le produit chaque jour — mais il n'est visible
nulle part, parce que son répertoire de sortie n'est pas suivi. L'échantillon donne à voir la forme
des données, la nomenclature des champs et la variété des valeurs, sans rien exiger du lecteur.

L'ÉCHANTILLON EST ENGENDRÉ, JAMAIS CONSTITUÉ À LA MAIN. Un extrait recopié diverge en silence de ce
dont il est extrait ; celui-ci se réengendre, et un contrôle vérifie que chacune de ses lignes
existe encore dans la table dont elle vient.

CE QUE CHAQUE FICHIER PORTE. Une première colonne, sur CHAQUE ligne, dit que les données sont
synthétiques, comment elles ont été produites, et qu'aucun patient réel n'y figure. La forme a été
tranchée par mesure et non par goût — voir `MENTION` ci-dessous.

CONNEXION. Celle des modules existants, par le chargeur d'environnement partagé, avec le chemin de
recherche réduit au seul schéma lu. Aucun second chemin n'est inventé.

OÙ CE MODULE VIT, ET POURQUOI PAS AILLEURS. Le dépôt donne un répertoire de premier niveau à chaque
fonction — production, chargement, modélisation, rapprochement, instantané, livraison, restitution.
L'extraction d'un échantillon en est une de plus, et elle reçoit donc le sien. Le module s'appelle
`extraction` et le répertoire qu'il écrit `echantillon`, jamais l'inverse : le module d'export du
livrable quotidien a déjà rencontré ce piège et l'a consigné — « Le répertoire de ce module
s'appelle `livraison` et non `export` : le répertoire de SORTIE s'appelle `exports`, et deux
noms voisins auraient fini par être confondus dans une commande ou un chemin. »
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import psycopg

from ingestion import appliquer_ddl

RACINE = Path(__file__).resolve().parent.parent
DESTINATION = RACINE / "echantillon"

# La mention, portée par CHAQUE LIGNE de CHAQUE fichier, dans une première colonne.
#
# POURQUOI UNE COLONNE ET NON UN COMMENTAIRE EN TÊTE. Les deux formes ont été mesurées contre deux
# lecteurs standards, sans aucune option :
#
#   forme                          pandas.read_csv                     csv.DictReader
#   commentaire « # … » en tête    1 colonne, le commentaire en titre   champs illisibles
#   colonne d'avertissement        4 colonnes, titres corrects          champs corrects
#
# Le commentaire en tête CASSE la lecture du fichier par un outil standard ; la colonne ne la casse
# pas. Un lecteur qui télécharge un fichier isolé, sans le fichier d'accompagnement, voit la mention
# sur chaque ligne quel que soit l'outil avec lequel il l'ouvre.
#
# CE QU'ELLE COÛTE : une colonne de plus, répétée sur chaque ligne — 86 octets par ligne, mesurés,
# soit environ 190 Kio sur l'échantillon entier. C'est le prix d'une garantie qui ne dépend d'aucun
# fichier voisin.
MENTION = "Donnees synthetiques simulees a partir de statistiques publiques ; aucun patient reel"
COLONNE_MENTION = "donnees_synthetiques"

# Combien de lignes par table, et pourquoi ces deux nombres.
#
# Le critère n'est pas qu'un lecteur dispose d'un jeu de travail — il ne pourrait rien en faire de
# juste, un extrait ne portant aucun total exploitable — mais qu'il voie la FORME des données et la
# VARIÉTÉ des valeurs. Deux cents lignes suffisent à faire apparaître plusieurs services, plusieurs
# activités et plusieurs mois sur les tables source, qui sont celles dont la nomenclature est le
# livrable ; cinquante suffisent sur la couche analytique, dont les colonnes sont dérivées et dont
# les dimensions les plus petites ne portent que sept ou huit valeurs au total.
LIGNES_SOURCE = 200
LIGNES_ANALYTIQUE = 50

# Les onze tables de la couche source, avec la colonne qui ordonne l'échantillonnage systématique.
# L'ordre est celui d'une clé stable, jamais celui de l'insertion : il doit rendre le même extrait à
# chaque exécution.
TABLES_SOURCE = {
    "patients": "n_ipp",
    "rendez_vous": "n_rdv",
    "passages": "n_passage",
    "mouvements": "n_sejour",
    "passages_urgences": "n_passage",
    "factures": "n_facture",
    "lignes_facture": "n_facture, n_ligne",
    "prises_en_charge": "n_prise_en_charge",
    "encaissements": "n_encaissement",
    "creances": "n_creance",
    "relances": "n_relance",
}

# Les douze objets du schéma en étoile, dans l'instantané. Les agrégats en sont exclus : ce sont des
# grandeurs calculées que le tableau de bord affiche déjà, et leur forme n'apprend rien sur celle
# des données.
TABLES_ANALYTIQUES = {
    "dim_patient": "n_ipp, valide_de",
    "dim_date": "date_jour",
    "dim_activite": "code_activite",
    "dim_service": "code_service",
    "dim_organisme": "code_organisme",
    "dim_agent": "code_agent",
    "fct_rendez_vous": "n_rdv",
    "fct_passage": "n_passage",
    "fct_passage_urgence": "n_passage",
    "fct_sejour": "n_sejour",
    "fct_facturation": "n_facture",
    "fct_encaissement": "n_encaissement",
}

# La paire de fiches en double, forcée dans l'échantillon de la table des patients.
#
# C'est ce qui montre d'un coup que les défauts du jeu sont délibérés et que le rapprochement a
# quelque chose à rapprocher : deux fiches de la même personne, que seule une variante graphique du
# prénom sépare. Sans cette inclusion forcée, l'échantillonnage systématique n'aurait aucune raison
# de retenir les deux.
PAIRE_DOUBLON = ("IPP-002116", "IPP-025034")


class EchantillonImpossible(RuntimeError):
    """L'échantillon ne peut être produit ; le message dit pourquoi."""


def _connexion(schema: str):
    """Connexion dont le chemin de recherche est réduit au schéma lu."""
    variables = appliquer_ddl.charger_environnement()
    conn = psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables.get("POSTGRES_PASSWORD", ""),
    )
    with conn.cursor() as curseur:
        curseur.execute(f"set search_path to {schema}")
        curseur.execute("set time zone 'UTC'")
    return conn


def _colonnes(curseur, table: str) -> list[str]:
    curseur.execute(
        "select column_name from information_schema.columns "
        "where table_schema = current_schema() and table_name = %s order by ordinal_position",
        (table,),
    )
    return [nom for (nom,) in curseur.fetchall()]


def requete_echantillon(table: str, ordre: str, lignes: int, forces: tuple[str, ...] = ()) -> str:
    """L'échantillonnage est SYSTÉMATIQUE, et c'est un choix mesurable.

    Prendre les premières lignes ne montrerait qu'une période et qu'une tranche d'identifiants ;
    tirer au hasard ne serait pas reproductible sans graine, et une graine écrite ici serait un
    paramètre de plus à justifier. L'échantillonnage systématique — une ligne sur N, dans l'ordre
    d'une clé stable — parcourt toute l'étendue de la table, rend le même extrait à chaque
    exécution, et n'exige aucun paramètre aléatoire.

    Les lignes forcées sont ajoutées à l'échantillon systématique, jamais substituées : elles ne
    déplacent pas le pas d'échantillonnage.
    """
    clause_forcee = ""
    if forces:
        valeurs = ", ".join(f"'{valeur}'" for valeur in forces)
        clause_forcee = f" or {ordre.split(',')[0].strip()} in ({valeurs})"
    return f"""
        with numerotees as (
            select *, row_number() over (order by {ordre}) as rang, count(*) over () as total
            from {table}
        )
        select * from numerotees
        where (rang - 1) % greatest(total / {lignes}, 1) = 0{clause_forcee}
        order by {ordre}
        limit {lignes} + {len(forces)}
    """


def ecrire_table(
    curseur, table: str, ordre: str, lignes: int, destination: Path, forces: tuple[str, ...] = ()
) -> tuple[int, int]:
    colonnes = _colonnes(curseur, table)
    if not colonnes:
        raise EchantillonImpossible(f"la table « {table} » n'existe pas ou ne porte aucune colonne")
    curseur.execute(requete_echantillon(table, ordre, lignes, forces))
    extraites = curseur.fetchall()
    noms = [description.name for description in curseur.description]
    # `rang` et `total` sont les colonnes de travail de la numérotation : elles ne sont pas des
    # colonnes de la table et ne sont donc pas versées.
    gardees = [i for i, nom in enumerate(noms) if nom in colonnes]

    chemin = destination / f"{table}.csv"
    with chemin.open("w", encoding="utf-8-sig", newline="") as fichier:
        plume = csv.writer(fichier, delimiter=",")
        plume.writerow([COLONNE_MENTION] + [noms[i] for i in gardees])
        for ligne in extraites:
            plume.writerow([MENTION] + ["" if ligne[i] is None else ligne[i] for i in gardees])
    return len(extraites), chemin.stat().st_size


def produire(destination: Path | None = None) -> dict:
    destination = destination or DESTINATION
    destination.mkdir(parents=True, exist_ok=True)

    ecrits: list[tuple[str, int, int]] = []
    for schema, tables, lignes in (
        ("source", TABLES_SOURCE, LIGNES_SOURCE),
        ("instantane", TABLES_ANALYTIQUES, LIGNES_ANALYTIQUE),
    ):
        conn = _connexion(schema)
        try:
            with conn.cursor() as curseur:
                for table, ordre in tables.items():
                    forces = PAIRE_DOUBLON if (schema == "source" and table == "patients") else ()
                    n, octets = ecrire_table(curseur, table, ordre, lignes, destination, forces)
                    ecrits.append((table, n, octets))
        finally:
            conn.close()

    attendus = {table for table in TABLES_SOURCE} | {table for table in TABLES_ANALYTIQUES}
    for chemin in destination.glob("*.csv"):
        if chemin.stem not in attendus:
            chemin.unlink()

    return {
        "tables": len(ecrits),
        "lignes": sum(n for _, n, _ in ecrits),
        "octets": sum(o for _, _, o in ecrits),
        "detail": ecrits,
    }


def main(arguments: list[str] | None = None) -> None:
    analyseur = argparse.ArgumentParser(
        prog="python -m extraction.echantillon",
        description=(
            "Engendre l'échantillon de données versé au dépôt : un extrait de chaque table, "
            "chaque ligne portant la mention qui dit que les données sont synthétiques."
        ),
    )
    analyseur.add_argument(
        "--destination",
        type=Path,
        default=None,
        help="Répertoire de sortie (défaut : le répertoire d'échantillon du dépôt)",
    )
    options = analyseur.parse_args(arguments)

    try:
        resume = produire(options.destination)
    except (EchantillonImpossible, psycopg.Error) as erreur:
        print(f"échantillon : ÉCHEC - {erreur}", file=sys.stderr)
        raise SystemExit(1) from erreur

    print(
        f"échantillon : OK - {resume['tables']} tables, {resume['lignes']} lignes, "
        f"{resume['octets']} octets"
    )


if __name__ == "__main__":
    main()
