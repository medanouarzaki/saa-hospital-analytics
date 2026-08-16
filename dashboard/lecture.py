"""Point d'accès unique du tableau de bord à la base.

Aucune page n'ouvre de connexion : elles passent toutes par ce module. Deux raisons, dont la
seconde est une garantie et non une convention.

D'abord, la mise en cache. Elle est indexée sur l'horodatage du dernier rafraîchissement, lu dans
la table d'état de l'instantané : un rafraîchissement invalide donc le cache par construction. Une
mise en cache indexée sur une durée fixe masquerait le rafraîchissement pendant cette durée, ce qui
contredirait la raison d'être de l'instantané — un état daté, connu de celui qui le lit.

La configuration de connexion vient de `charger_environnement`, le lecteur d'environnement partagé
du dépôt : mêmes variables, mêmes valeurs par défaut, même fichier. Ce module n'appelle pas le
connecteur du chargeur de fichiers, qui importe au passage la machinerie de chargement et son
registre de champs — mesuré : ce registre n'existe pas dans l'image du service, et l'import y
échoue. Le tableau de bord ne charge rien ; il n'a besoin que de la configuration.

Ensuite, la restriction de couche. Le tableau de bord ne lit que le schéma d'instantané, et cette
restriction est STRUCTURELLE : chaque connexion ouverte ici fixe son chemin de recherche à ce seul
schéma. Une requête qui nommerait sans le qualifier un objet d'une autre couche échoue à
l'exécution, avec une erreur d'objet inexistant. Ce n'est donc pas un contrôle textuel que l'on
pourrait contourner par inadvertance, mais une propriété du serveur, éprouvée par un contrôle.
"""

from __future__ import annotations

import pandas as pd
import psycopg
import streamlit as st

from ingestion import appliquer_ddl

SCHEMA = "instantane"
TABLE_ETAT = "instantane_etat"


def _connexion():
    """Ouvre une connexion dont le chemin de recherche est réduit au seul schéma d'instantané.

    `pg_catalog` reste implicitement accessible — le serveur l'ajoute toujours en tête — ce qui
    permet aux fonctions et types de base de fonctionner sans permettre d'atteindre les couches de
    la chaîne de transformation.
    """
    variables = appliquer_ddl.charger_environnement()
    conn = psycopg.connect(
        host=variables["POSTGRES_HOST"],
        port=variables["POSTGRES_PORT"],
        dbname=variables["POSTGRES_DB"],
        user=variables["POSTGRES_USER"],
        password=variables.get("POSTGRES_PASSWORD", ""),
    )
    with conn.cursor() as curseur:
        curseur.execute(f"set search_path to {SCHEMA}")
        # Fuseau fixé : sans cela, l'heure extraite d'un horodatage dépendrait du fuseau de la
        # session, et une répartition horaire changerait selon qui l'interroge.
        curseur.execute("set time zone 'UTC'")
    return conn


def etat() -> dict:
    """Horodatage du rafraîchissement et date de référence des données.

    Non mis en cache : c'est la valeur qui sert de clé au cache de tout le reste, et la mettre en
    cache elle-même reviendrait à ne jamais voir un rafraîchissement.
    """
    conn = _connexion()
    try:
        with conn.cursor() as curseur:
            curseur.execute(
                f"select max(rafraichi_le), max(date_reference_donnees) from {TABLE_ETAT}"
            )
            rafraichi_le, date_reference = curseur.fetchone()
    finally:
        conn.close()
    return {"rafraichi_le": rafraichi_le, "date_reference": date_reference}


@st.cache_data(show_spinner=False)
def _interroger(requete: str, horodatage) -> pd.DataFrame:
    """Exécute une requête et rend un tableau de données.

    `horodatage` n'est pas employé dans le corps : il n'est là que pour entrer dans la clé de
    cache. C'est ce qui lie la validité du cache à celle de l'instantané — quand l'horodatage
    change, la clé change, et la requête est réexécutée.
    """
    conn = _connexion()
    try:
        with conn.cursor() as curseur:
            curseur.execute(requete)
            colonnes = [description[0] for description in curseur.description]
            lignes = curseur.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(lignes, columns=colonnes)


def interroger(requete: str) -> pd.DataFrame:
    """Point d'entrée des pages. La clé de cache est prise ici, à chaque appel."""
    return _interroger(requete, etat()["rafraichi_le"])
