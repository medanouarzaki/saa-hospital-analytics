"""Contrôle bloquant : aucun champ synthétique ne prend une valeur structurellement possible
dans son espace réel.

POURQUOI CE FICHIER EXISTE.

Le jeu de données est simulé, mais « simulé » ne suffit pas : une valeur inventée peut tomber dans
l'espace des valeurs réellement émises. Un numéro de téléphone tiré sur un préfixe attribué **est le
numéro de quelqu'un** — pas d'un patient, de n'importe qui — et une adresse de messagerie chez un
fournisseur exploité peut être une boîte réelle. Publiés à côté d'un nom, d'une adresse et d'une
ville, ils se lisent comme un fichier nominatif et peuvent faire sonner un téléphone.

CE QUE CE FICHIER VÉRIFIE : que chaque champ recensé porte une propriété de STRUCTURE qui le rend
impossible dans son espace réel. Une impossibilité de structure, jamais une non-attribution : une
plage non attribuée aujourd'hui peut être ouverte demain, et la garantie tomberait en silence sans
que personne ne touche au dépôt. Une longueur qui n'existe pas dans un plan de numérotation, ou un
domaine que la norme interdit d'enregistrer, ne changent pas.

CE QU'IL NE VÉRIFIE PAS : les noms, prénoms, adresses de voie et villes. **Le critère est celui-ci :
un identifiant désigne une personne ou un compte, un attribut la décrit.** « Fatima Amrani » et
« 113 Boulevard Mohammed V » décrivent une fiche sans désigner qui que ce soit — des milliers de
personnes portent ce nom, et une voie n'est l'adresse de personne en particulier. Les exclure du
périmètre est un choix, et le retirer de ces colonnes viderait le jeu du réalisme qui fait tout son
intérêt.

Aucun travail au niveau du module : ni connexion, ni lecture de variable d'environnement, ni requête
à l'import. Le fichier se collecte sur un clone frais sans base ni variable exportée.

Aucun littéral de volumétrie : le contrôle porte sur la forme de chaque valeur, jamais sur leur
nombre.
"""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

import psycopg
import pytest

RACINE = Path(__file__).resolve().parent.parent
APPLIQUER_DDL = RACINE / "ingestion" / "appliquer_ddl.py"
ECHANTILLON = RACINE / "echantillon"

# La longueur d'un numéro marocain en forme nationale : le zéro de tête et neuf chiffres
# significatifs. C'est cette valeur, et elle seule, qu'un numéro synthétique ne doit pas avoir.
LONGUEUR_NUMERO_NATIONAL = 10

# La longueur de l'immatriculation à la caisse nationale de sécurité sociale.
LONGUEUR_IMMATRICULATION = 9

# Les domaines que la RFC 2606 réserve et interdit d'enregistrer. `example.com`, `example.net` et
# `example.org` sont nommés ; `.invalid` est un domaine de premier niveau réservé, si bien que
# n'importe quel nom sous ce suffixe l'est aussi.
MOTIF_DOMAINE_RESERVE = re.compile(r"@(example\.(com|net|org)|[A-Za-z0-9-]+\.invalid)$")


def _sans_lettre(valeur: str) -> bool:
    return not any(caractere.isalpha() for caractere in valeur)


# Le recensement, et pour chaque champ la propriété de structure qui l'exclut de son espace réel.
# Chaque entrée porte : la table de la couche source, la colonne, l'espace réel qu'elle pourrait
# recouvrir, le prédicat qui doit être vrai de toute valeur, et l'énoncé de la propriété tel qu'il
# figure au message d'échec.
CHAMPS = (
    (
        "patients",
        "telephone_1",
        "plan de numérotation marocain",
        lambda v: len(v) != LONGUEUR_NUMERO_NATIONAL,
        f"un numéro national compte exactement {LONGUEUR_NUMERO_NATIONAL} chiffres",
    ),
    (
        "patients",
        "telephone_2",
        "plan de numérotation marocain",
        lambda v: len(v) != LONGUEUR_NUMERO_NATIONAL,
        f"un numéro national compte exactement {LONGUEUR_NUMERO_NATIONAL} chiffres",
    ),
    (
        "patients",
        "telephone_3",
        "plan de numérotation marocain",
        lambda v: len(v) != LONGUEUR_NUMERO_NATIONAL,
        f"un numéro national compte exactement {LONGUEUR_NUMERO_NATIONAL} chiffres",
    ),
    (
        "patients",
        "telephone_4",
        "plan de numérotation marocain",
        lambda v: len(v) != LONGUEUR_NUMERO_NATIONAL,
        f"un numéro national compte exactement {LONGUEUR_NUMERO_NATIONAL} chiffres",
    ),
    (
        "patients",
        "email",
        "espace des noms de domaine enregistrables",
        lambda v: bool(MOTIF_DOMAINE_RESERVE.search(v)),
        "le domaine doit être réservé par la RFC 2606 : example.com, example.net,\n"
        "example.org, ou un nom sous .invalid",
    ),
    (
        "patients",
        "n_piece_identite",
        "carte nationale d'identité marocaine",
        _sans_lettre,
        "une carte nationale porte une ou deux lettres ; une suite purement\n"
        "numérique n'en est pas une",
    ),
    (
        "patients",
        "police",
        "immatriculation de sécurité sociale",
        lambda v: len(v) != LONGUEUR_IMMATRICULATION,
        f"une immatriculation compte exactement {LONGUEUR_IMMATRICULATION} chiffres",
    ),
    (
        "patients",
        "n_assure",
        "immatriculation de sécurité sociale",
        lambda v: len(v) != LONGUEUR_IMMATRICULATION,
        f"une immatriculation compte exactement {LONGUEUR_IMMATRICULATION} chiffres",
    ),
    (
        "patients",
        "num_inscription",
        "immatriculation de sécurité sociale",
        lambda v: len(v) != LONGUEUR_IMMATRICULATION,
        f"une immatriculation compte exactement {LONGUEUR_IMMATRICULATION} chiffres",
    ),
    (
        "patients",
        "n_ipp",
        "identifiants administratifs purement numériques",
        lambda v: not _sans_lettre(v),
        "un identifiant interne porte un préfixe alphabétique qu'aucun registre national n'emploie",
    ),
    (
        "prises_en_charge",
        "n_assure",
        "immatriculation de sécurité sociale",
        lambda v: not _sans_lettre(v),
        "un identifiant interne porte un préfixe alphabétique qu'aucun registre national n'emploie",
    ),
)


def _charger_module(chemin: Path):
    spec = importlib.util.spec_from_file_location(chemin.stem, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _connexion() -> psycopg.Connection:
    """Ouverte à l'appel, jamais à l'import."""
    variables = _charger_module(APPLIQUER_DDL).charger_environnement()
    try:
        return psycopg.connect(
            host=variables["POSTGRES_HOST"],
            port=variables["POSTGRES_PORT"],
            dbname=variables["POSTGRES_DB"],
            user=variables["POSTGRES_USER"],
            password=variables.get("POSTGRES_PASSWORD", ""),
            connect_timeout=5,
        )
    except psycopg.OperationalError as exc:
        pytest.fail(f"connexion impossible à la base ({exc}) : la couche source doit être chargée")


def _valeurs_en_base(table: str, colonne: str) -> list[str]:
    connexion = _connexion()
    try:
        with connexion.cursor() as curseur:
            curseur.execute(
                f"select {colonne} from source.{table} "  # noqa: S608
                f"where {colonne} is not null and {colonne} <> ''"
            )
            return [valeur for (valeur,) in curseur.fetchall()]
    finally:
        connexion.close()


def _valeurs_dans_l_echantillon(table: str, colonne: str) -> list[str]:
    fichier = ECHANTILLON / f"{table}.csv"
    if not fichier.exists():
        return []
    with fichier.open(encoding="utf-8-sig", newline="") as flux:
        lignes = list(csv.DictReader(flux))
    if not lignes or colonne not in lignes[0]:
        return []
    return [ligne[colonne] for ligne in lignes if ligne[colonne]]


def _fautives(valeurs: list[str], predicat) -> list[str]:
    return sorted({valeur for valeur in valeurs if not predicat(valeur)})


@pytest.mark.parametrize(
    ("table", "colonne", "espace_reel", "predicat", "propriete"),
    CHAMPS,
    ids=lambda valeur: valeur if isinstance(valeur, str) else "",
)
def test_aucune_valeur_n_est_possible_dans_son_espace_reel(
    table: str, colonne: str, espace_reel: str, predicat, propriete: str
) -> None:
    """Aucun champ synthétique ne prend une valeur structurellement possible dans son espace réel.

    La propriété s'exerce sur les DONNÉES PRODUITES — la couche source de la base et les fichiers
    versés au dépôt — et non sur la configuration qui les engendre : une configuration corrigée dont
    la sortie ne l'est pas laisserait passer exactement ce que ce contrôle doit attraper.
    """
    valeurs = _valeurs_en_base(table, colonne)
    assert valeurs, (
        f"aucune valeur de source.{table}.{colonne} : la couche source est-elle chargée ?"
    )

    fautives = _fautives(valeurs, predicat)
    apercu = ", ".join(fautives[:5])
    assert not fautives, (
        f"source.{table}.{colonne} : {len(fautives)} valeur(s) distincte(s) possibles dans "
        f"l'espace réel ({espace_reel}) — {apercu}\n"
        f"propriété violée : {propriete}"
    )

    versees = _valeurs_dans_l_echantillon(table, colonne)
    fautives_versees = _fautives(versees, predicat)
    apercu_verse = ", ".join(fautives_versees[:5])
    assert not fautives_versees, (
        f"echantillon/{table}.csv, colonne {colonne} : {len(fautives_versees)} valeur(s) "
        f"distincte(s) possibles dans l'espace réel ({espace_reel}) — {apercu_verse}\n"
        f"propriété violée : {propriete}"
    )
