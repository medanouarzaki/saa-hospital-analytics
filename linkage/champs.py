"""Registre des champs d'identité comparés pour le rapprochement de patients.

Ce module est la source unique de vérité sur les champs comparés : pour
chaque champ retenu, la colonne de marts.dim_patient qui le porte, la
variante de normalisation qui lui est appliquée avant comparaison, et une
justification ancrée sur une grandeur mesurée. Les colonnes écartées sont
également déclarées, avec le motif mesuré de leur exclusion, pour que
l'absence d'un champ dans les comparaisons soit une décision documentée et
non un oubli.
"""

from enum import Enum
from typing import NamedTuple


class Normalisation(Enum):
    """Variante de normalisation textuelle appliquée à un champ."""

    AUCUNE = "aucune"
    V1 = "v1"
    V2 = "v2"


class ChampCompare(NamedTuple):
    colonne: str
    normalisation: Normalisation
    justification: str


class ColonneEcartee(NamedTuple):
    colonne: str
    motif: str


# Les douze champs comparés, dans l'ordre où ils entrent dans le modèle de
# rapprochement.
CHAMPS_COMPARES: dict[str, ChampCompare] = {
    "nom": ChampCompare(
        colonne="nom",
        normalisation=Normalisation.V2,
        justification=(
            "le tri des composants du prénom absorbe l'inversion des "
            "parties : m passe de 0,699 à 0,945 à similarité 0,90, u reste "
            "inchangé à 0,029"
        ),
    ),
    "nom_famille_1": ChampCompare(
        colonne="nom_famille_1",
        normalisation=Normalisation.V1,
        justification="aucun désaccord observé sur les paires vraies ; u = 0,050",
    ),
    "nom_famille_2": ChampCompare(
        colonne="nom_famille_2",
        normalisation=Normalisation.V1,
        justification=(
            "aucun désaccord quand les deux côtés sont renseignés ; vide "
            "d'un côté sur 85 paires vraies, ce qui exige un niveau de vacuité"
        ),
    ),
    "date_naissance": ChampCompare(
        colonne="date_naissance",
        normalisation=Normalisation.AUCUNE,
        justification=(
            "la normalisation textuelle découperait la date en jetons et "
            "le tri des composants la détruirait"
        ),
    ),
    "type_piece_identite": ChampCompare(
        colonne="type_piece_identite",
        normalisation=Normalisation.V1,
        justification="n'entre qu'en clé composite avec le numéro de pièce",
    ),
    "n_piece_identite": ChampCompare(
        colonne="n_piece_identite",
        normalisation=Normalisation.V1,
        justification="u = 2,4e-06 ; le champ le plus discriminant du jeu",
    ),
    "telephone_1": ChampCompare(
        colonne="telephone_1",
        normalisation=Normalisation.V1,
        justification="m = 0,729 ; u = 9,7e-05",
    ),
    "adresse": ChampCompare(
        colonne="adresse",
        normalisation=Normalisation.V1,
        justification=(
            "comparaison exacte seulement : la comparaison floue multiplie "
            "u par 164 pour 14 paires vraies supplémentaires"
        ),
    ),
    "email": ChampCompare(
        colonne="email",
        normalisation=Normalisation.V1,
        justification="u = 2,6e-04 ; vide sur 78% de la population",
    ),
    "nom_pere": ChampCompare(
        colonne="nom_pere",
        normalisation=Normalisation.V1,
        justification="u = 0,050 ; indépendant des autres champs nominaux, rapport mesuré 1,0007",
    ),
    "nom_mere": ChampCompare(
        colonne="nom_mere",
        normalisation=Normalisation.V1,
        justification="u = 0,050",
    ),
    "quartier": ChampCompare(
        colonne="quartier",
        normalisation=Normalisation.V1,
        justification="u = 0,050 ; vide sur 31% de la population",
    ),
    "ville": ChampCompare(
        colonne="ville",
        normalisation=Normalisation.V1,
        justification=(
            "rapport global faible, 2,13, mais un accord sur une valeur "
            "rare porte 17 à 36 fois l'information d'un accord sur la "
            "valeur modale : entre avec ajustement de fréquence"
        ),
    ),
}

# Les colonnes écartées, avec leur motif mesuré d'exclusion.
COLONNES_ECARTEES: dict[str, ColonneEcartee] = {
    "etat": ColonneEcartee(
        colonne="etat",
        motif="un accord n'y apprend presque rien : rapport mesuré 1,10",
    ),
    "etat_naissance": ColonneEcartee(
        colonne="etat_naissance",
        motif=(
            "un accord n'y apprend presque rien (rapport mesuré 1,29) et "
            "la colonne est une copie programmatique de etat, égalité "
            "ligne à ligne sur toute la population"
        ),
    ),
    "pays_naissance": ColonneEcartee(
        colonne="pays_naissance",
        motif="un accord n'y apprend presque rien : rapport mesuré 1,15",
    ),
    "ville_naissance": ColonneEcartee(
        colonne="ville_naissance",
        motif="copie programmatique de ville, égalité ligne à ligne sur toute la population",
    ),
    "quartier_naissance": ColonneEcartee(
        colonne="quartier_naissance",
        motif="même formule de génération que quartier",
    ),
    "code_postal": ColonneEcartee(
        colonne="code_postal",
        motif="dérivé de ville par correspondance",
    ),
    "telephone_2": ColonneEcartee(
        colonne="telephone_2",
        motif="dénominateur de 6 à 45 paires observées : instable",
    ),
    "telephone_3": ColonneEcartee(
        colonne="telephone_3",
        motif="dénominateur de 6 à 45 paires observées : instable",
    ),
    "telephone_4": ColonneEcartee(
        colonne="telephone_4",
        motif="dénominateur de 6 à 45 paires observées : instable",
    ),
}


def noms_champs_compares() -> list[str]:
    return list(CHAMPS_COMPARES.keys())


def noms_colonnes_ecartees() -> list[str]:
    return list(COLONNES_ECARTEES.keys())
