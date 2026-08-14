"""Tests du schéma linkage (linkage/ddl/).

Exige une base PostgreSQL avec le schéma linkage déjà appliqué
(`uv run python -m linkage.appliquer_ddl`). Aucun skip silencieux : un
schéma absent ou non appliqué fait échouer ce fichier, pas le sauter.

Aucune insertion de ce fichier n'est jamais commise : la connexion est
explicitement annulée (`rollback`) en fin de test, jamais validée
(`commit`) — ce fichier ne doit laisser aucune trace dans la base, réussite
ou échec d'insertion confondus.
"""

import psycopg
import pytest

from linkage.champs import COMPARAISONS
from linkage.population import _connexion

PREFIXE_NIVEAU = "niveau_"
TABLES_ATTENDUES = {"paires_candidates", "grappes_identite", "evaluation"}


@pytest.fixture
def connexion():
    with _connexion() as cnx:
        yield cnx
        cnx.rollback()


def _colonnes_paires_candidates(connexion) -> list[str]:
    """Colonnes actuelles de linkage.paires_candidates, introspectées plutôt
    que recopiées : les tests d'insertion ci-dessous restent valides même si
    le nombre ou le nom des colonnes de niveau change (mutation de la DDL),
    au lieu de dépendre d'une liste figée qui romprait pour une raison
    étrangère à la propriété testée.
    """
    with connexion.cursor() as curseur:
        curseur.execute(
            "select column_name, data_type from information_schema.columns "
            "where table_schema = 'linkage' and table_name = 'paires_candidates' "
            "order by ordinal_position"
        )
        return curseur.fetchall()


def _inserer_paire(connexion, n_ipp_1: str, n_ipp_2: str) -> None:
    """Insère une paire en construisant la liste de colonnes et de valeurs à
    partir du schéma réellement présent, pas d'une liste écrite en dur.
    """
    colonnes = _colonnes_paires_candidates(connexion)
    valeurs = []
    for nom, type_donnee in colonnes:
        if nom in ("n_ipp_1", "n_ipp_2"):
            valeurs.append(n_ipp_1 if nom == "n_ipp_1" else n_ipp_2)
        elif type_donnee == "text":
            valeurs.append("test")
        elif type_donnee == "integer":
            valeurs.append(0)
        else:
            valeurs.append(0.5)
    noms_colonnes = ", ".join(nom for nom, _ in colonnes)
    marqueurs = ", ".join(["%s"] * len(colonnes))
    with connexion.cursor() as curseur:
        curseur.execute(
            f"insert into linkage.paires_candidates ({noms_colonnes}) values ({marqueurs})",
            valeurs,
        )


def test_les_trois_tables_existent(connexion):
    with connexion.cursor() as curseur:
        curseur.execute(
            "select table_name from information_schema.tables where table_schema = 'linkage'"
        )
        tables = {ligne[0] for ligne in curseur.fetchall()}
    assert tables == TABLES_ATTENDUES


def test_colonnes_de_niveau_correspondent_exactement_aux_comparaisons(connexion):
    with connexion.cursor() as curseur:
        curseur.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'linkage' and table_name = 'paires_candidates'"
        )
        colonnes = {ligne[0] for ligne in curseur.fetchall()}
    colonnes_niveau = {
        colonne[len(PREFIXE_NIVEAU) :] for colonne in colonnes if colonne.startswith(PREFIXE_NIVEAU)
    }
    assert colonnes_niveau == set(COMPARAISONS.keys())


def test_contrainte_ordre_canonique_rejette_paire_inversee(connexion):
    with connexion.cursor() as curseur:
        curseur.execute("select count(*) from linkage.paires_candidates")
        avant = curseur.fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        _inserer_paire(connexion, "B", "A")
    connexion.rollback()

    with connexion.cursor() as curseur:
        curseur.execute("select count(*) from linkage.paires_candidates")
        apres = curseur.fetchone()[0]
    assert apres == avant, "l'insertion inversée rejetée n'aurait jamais dû rester commise"


def test_contrainte_ordre_canonique_rejette_paire_reflexive(connexion):
    with connexion.cursor() as curseur:
        curseur.execute("select count(*) from linkage.paires_candidates")
        avant = curseur.fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        _inserer_paire(connexion, "A", "A")
    connexion.rollback()

    with connexion.cursor() as curseur:
        curseur.execute("select count(*) from linkage.paires_candidates")
        apres = curseur.fetchone()[0]
    assert apres == avant, "l'insertion réflexive rejetée n'aurait jamais dû rester commise"


def test_les_trois_tables_ne_font_aucune_hypothese_sur_leur_contenu(connexion):
    # Observe seulement : ne compare le compte à aucune valeur, pour rester vrai
    # que les tables soient vides ou déjà peuplées à ce stade.
    with connexion.cursor() as curseur:
        for table in TABLES_ATTENDUES:
            curseur.execute(f"select count(*) from linkage.{table}")
            nb = curseur.fetchone()[0]
            assert nb >= 0
