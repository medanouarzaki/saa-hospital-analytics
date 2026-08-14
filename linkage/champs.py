"""Registre des champs d'identité comparés pour le rapprochement de patients.

Ce module est la source unique de vérité sur les champs comparés : pour
chaque champ retenu, la colonne de marts.dim_patient qui le porte, la
variante de normalisation qui lui est appliquée avant comparaison, et une
justification ancrée sur une grandeur mesurée. Les colonnes écartées sont
également déclarées, avec le motif mesuré de leur exclusion, pour que
l'absence d'un champ dans les comparaisons soit une décision documentée et
non un oubli.

Deux notions distinctes cohabitent ici, et ne dénotent pas la même chose :
  - une COLONNE COMPARÉE (`CHAMPS_COMPARES`) est une colonne de
    marts.dim_patient soumise à normalisation avant comparaison ;
  - une COMPARAISON (`COMPARAISONS`) est une unité du modèle de
    rapprochement, qui consomme une ou plusieurs colonnes comparées.
Onze comparaisons consomment chacune une seule colonne. La douzième,
la comparaison composite pièce d'identité, consomme deux colonnes
(`type_piece_identite` et `n_piece_identite`) : ces deux colonnes ne
prennent leur sens qu'ensemble, un même numéro pouvant être porté par des
pièces de nature différente sans désigner la même identité (voir la
justification de `COMPARAISONS["piece_identite"]`). D'où treize colonnes
comparées pour douze comparaisons : les deux nombres sont corrects et
répondent à des questions différentes.
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


class Comparaison(NamedTuple):
    """Une unité du modèle de rapprochement : le nom de la comparaison, les
    colonnes comparées qu'elle consomme (une, sauf pour la comparaison
    composite pièce d'identité qui en consomme deux), et la justification de
    ce regroupement — distincte de la justification de normalisation portée
    par chaque colonne consommée.
    """

    nom: str
    colonnes: tuple[str, ...]
    justification: str


class ColonneEcartee(NamedTuple):
    colonne: str
    motif: str


# Les treize colonnes comparées, dans l'ordre où elles entrent dans le
# modèle de rapprochement. Ce ne sont pas treize comparaisons : voir
# COMPARAISONS ci-dessous, qui en regroupe deux (type_piece_identite et
# n_piece_identite) en une seule comparaison composite.
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


# La comparaison composite pièce d'identité : les deux colonnes qu'elle
# consomme, et sa justification propre, distincte de la justification de
# normalisation portée par chacune des deux colonnes dans CHAMPS_COMPARES.
# Mesure : le numéro seul et le couple (type, numéro) ont le même rappel,
# mais le couple produit seize paires en moins que le numéro seul — un
# numéro identique porté par deux types de pièce différents est une
# coïncidence numérique, pas une identité.
_COLONNES_COMPARAISON_PIECE_IDENTITE: tuple[str, str] = (
    "type_piece_identite",
    "n_piece_identite",
)

_JUSTIFICATION_COMPARAISON_PIECE_IDENTITE = (
    "le numéro seul et le couple (type, numéro) ont le même rappel, mais le "
    "couple produit seize paires en moins qu'une comparaison sur le numéro "
    "seul : un numéro identique porté par deux types de pièce différents "
    "est une coïncidence numérique, pas une identité"
)


def _construire_comparaisons() -> dict[str, Comparaison]:
    """Construit COMPARAISONS à partir de CHAMPS_COMPARES : chaque colonne
    comparée qui n'entre pas dans la comparaison composite pièce d'identité
    devient sa propre comparaison à une colonne, avec la justification de sa
    colonne ; les deux colonnes de la pièce d'identité sont retirées de ce
    traitement individuel et regroupées en une seule comparaison composite,
    avec sa justification propre. Rien n'est recompté à la main : le nombre
    de comparaisons et l'ensemble des colonnes qu'elles consomment découlent
    entièrement de CHAMPS_COMPARES et de ce regroupement.
    """
    colonnes_composite = set(_COLONNES_COMPARAISON_PIECE_IDENTITE)
    comparaisons: dict[str, Comparaison] = {
        nom_colonne: Comparaison(
            nom=nom_colonne,
            colonnes=(nom_colonne,),
            justification=champ.justification,
        )
        for nom_colonne, champ in CHAMPS_COMPARES.items()
        if nom_colonne not in colonnes_composite
    }
    comparaisons["piece_identite"] = Comparaison(
        nom="piece_identite",
        colonnes=_COLONNES_COMPARAISON_PIECE_IDENTITE,
        justification=_JUSTIFICATION_COMPARAISON_PIECE_IDENTITE,
    )
    return comparaisons


# Les douze comparaisons du modèle de rapprochement : onze consomment une
# seule colonne comparée, la douzième (pièce d'identité) en consomme deux.
COMPARAISONS: dict[str, Comparaison] = _construire_comparaisons()


def noms_champs_compares() -> list[str]:
    return list(CHAMPS_COMPARES.keys())


def noms_colonnes_ecartees() -> list[str]:
    return list(COLONNES_ECARTEES.keys())


def noms_comparaisons() -> list[str]:
    return list(COMPARAISONS.keys())


def colonnes_consommees() -> set[str]:
    """Union des colonnes comparées consommées par l'ensemble des
    comparaisons — une colonne par comparaison simple, deux pour la
    comparaison composite pièce d'identité.
    """
    consommees: set[str] = set()
    for comparaison in COMPARAISONS.values():
        consommees.update(comparaison.colonnes)
    return consommees
