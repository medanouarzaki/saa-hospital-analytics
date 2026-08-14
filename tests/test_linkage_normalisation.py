"""Tests des fonctions de normalisation textuelle du module de rapprochement.

Ce fichier n'exige aucune base : toutes les entrées sont écrites en dur.
"""

import pytest

from linkage.champs import CHAMPS_COMPARES, COLONNES_ECARTEES, Normalisation
from linkage.normalisation import (
    NormalisationNonApplicable,
    normaliser_champ,
    v1,
    v2,
)

# --- cas positifs connus, un par transformation prise seule -----------------


def test_v1_minuscules():
    assert v1("Ahmed BENANI") == "ahmed benani"


def test_v1_accents():
    assert v1("Éléonore Dûpont") == "eleonore dupont"


def test_v1_espaces_multiples():
    assert v1("Ahmed    Benani") == "ahmed benani"


def test_v1_ponctuation():
    assert v1("Benani, Ahmed.") == "benani ahmed"


def test_v1_espaces_de_bord():
    assert v1("  Ahmed Benani  ") == "ahmed benani"


def test_v2_composants_inverses():
    assert v2("Ahmed Karim") == "ahmed karim"
    assert v2("Karim Ahmed") == "ahmed karim"


# --- cas positif décisif ------------------------------------------------


def test_cas_decisif_inversion_prenom_compose():
    a = "Mohamed Amine"
    b = "Amine Mohamed"
    assert v2(a) == v2(b)
    assert v1(a) != v1(b)


# --- idempotence ----------------------------------------------------------


@pytest.mark.parametrize(
    "valeur",
    ["Ahmed Benani", "Éléonore, DÛPONT.", "  Karim   Amine  ", ""],
)
def test_v1_idempotent(valeur):
    once = v1(valeur)
    twice = v1(once)
    assert once == twice


@pytest.mark.parametrize(
    "valeur",
    ["Ahmed Benani", "Éléonore, DÛPONT.", "  Karim   Amine  ", ""],
)
def test_v2_idempotent(valeur):
    once = v2(valeur)
    twice = v2(once)
    assert once == twice


# --- préservation de la vacuité --------------------------------------------


def test_v1_preserve_vide():
    assert v1("") == ""
    assert v1(None) is None


def test_v2_preserve_vide():
    assert v2("") == ""
    assert v2(None) is None


def test_v1_ne_cree_pas_de_valeur_a_partir_du_vide():
    assert v1("   ") == "   "  # espace pur : traité comme vide, inchangé


def test_v2_ne_cree_pas_de_valeur_a_partir_du_vide():
    assert v2("   ") == "   "


def test_v1_ne_vide_pas_une_valeur_non_vide():
    assert v1("Ahmed Benani") != ""


def test_v2_ne_vide_pas_une_valeur_non_vide():
    assert v2("Ahmed Benani") != ""


# --- refus d'appliquer une normalisation à un champ déclaré sans normalisation --


def test_refus_normalisation_champ_sans_normalisation():
    assert CHAMPS_COMPARES["date_naissance"].normalisation is Normalisation.AUCUNE
    with pytest.raises(NormalisationNonApplicable):
        normaliser_champ("date_naissance", "1990-01-01")


def test_normaliser_champ_applique_v1():
    assert normaliser_champ("nom_famille_1", "BENANI") == "benani"


def test_normaliser_champ_applique_v2():
    assert normaliser_champ("nom", "Amine Mohamed") == normaliser_champ("nom", "Mohamed Amine")


def test_normaliser_champ_inconnu_leve():
    with pytest.raises(KeyError):
        normaliser_champ("champ_inexistant", "valeur")


# --- cohérence du registre ---------------------------------------------------


def test_chaque_champ_declare_porte_une_variante_connue():
    variantes_connues = {Normalisation.AUCUNE, Normalisation.V1, Normalisation.V2}
    for nom_champ, champ in CHAMPS_COMPARES.items():
        assert champ.normalisation in variantes_connues, nom_champ


def test_retenus_et_ecartees_sont_disjoints():
    retenus = set(CHAMPS_COMPARES.keys())
    ecartees = set(COLONNES_ECARTEES.keys())
    assert retenus.isdisjoint(ecartees)
