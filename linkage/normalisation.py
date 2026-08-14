"""Fonctions de normalisation textuelle pour le rapprochement de patients.

Deux variantes publiques :
  - v1 : minuscules, suppression des accents, réduction des espaces
    intérieurs à un seul, suppression des espaces de bord, suppression de
    la ponctuation.
  - v2 : v1, puis tri alphabétique des composants séparés par des espaces
    (absorbe l'inversion de l'ordre des composants d'un champ, par exemple
    un prénom composé écrit dans un ordre différent d'une source à l'autre).

Une valeur vide reste vide : aucune des deux fonctions ne transforme une
valeur absente ou vide en valeur présente.
"""

import string
import unicodedata

from linkage.champs import CHAMPS_COMPARES, Normalisation

_TABLE_PONCTUATION = str.maketrans({caractere: " " for caractere in string.punctuation})


def _est_vide(valeur: str | None) -> bool:
    return valeur is None or valeur.strip() == ""


def v1(valeur: str | None) -> str | None:
    """Minuscules, sans accents, ponctuation retirée, espaces réduits et
    coupés en bord. Une valeur vide ou absente reste inchangée.
    """
    if _est_vide(valeur):
        return valeur

    texte = valeur.lower()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = texte.translate(_TABLE_PONCTUATION)
    texte = " ".join(texte.split())
    return texte


def v2(valeur: str | None) -> str | None:
    """v1, puis tri alphabétique des composants séparés par des espaces.
    Une valeur vide ou absente reste inchangée.
    """
    if _est_vide(valeur):
        return valeur

    texte = v1(valeur)
    assert texte is not None  # valeur non vide -> v1 renvoie une chaîne
    composants = texte.split(" ")
    return " ".join(sorted(composants))


class NormalisationNonApplicable(ValueError):
    """Levée quand on tente d'appliquer une normalisation à un champ
    déclaré sans normalisation dans le registre."""


def normaliser_champ(nom_champ: str, valeur: str | None) -> str | None:
    """Applique au champ `nom_champ` la variante de normalisation déclarée
    pour lui dans le registre linkage.champs.CHAMPS_COMPARES.

    Refuse explicitement d'appliquer une normalisation à un champ déclaré
    sans normalisation (Normalisation.AUCUNE) : lever une exception plutôt
    que de faire silencieusement passer la valeur inchangée, pour qu'une
    tentative d'appel sur un tel champ soit visible et non un no-op muet.
    """
    if nom_champ not in CHAMPS_COMPARES:
        raise KeyError(f"champ non déclaré dans le registre : {nom_champ}")

    champ = CHAMPS_COMPARES[nom_champ]
    if champ.normalisation is Normalisation.AUCUNE:
        raise NormalisationNonApplicable(
            f"le champ '{nom_champ}' est déclaré sans normalisation dans le registre"
        )
    if champ.normalisation is Normalisation.V1:
        return v1(valeur)
    if champ.normalisation is Normalisation.V2:
        return v2(valeur)
    raise AssertionError(f"variante de normalisation non gérée : {champ.normalisation}")
