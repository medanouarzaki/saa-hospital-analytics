"""Tests du registre des champs et des comparaisons du module de rapprochement.

Ce fichier n'exige aucune base. Aucune valeur littérale n'y figure : chaque
propriété vérifiée compare des grandeurs dérivées du registre lui-même
(`linkage.champs`), jamais un nombre recopié à la main qui pourrait diverger
silencieusement du registre au fil de son évolution.
"""

from linkage.champs import CHAMPS_COMPARES, COLONNES_ECARTEES, COMPARAISONS


def test_colonnes_comparees_egale_colonnes_consommees():
    """Le nombre de colonnes comparées égale le nombre de colonnes
    distinctes consommées par l'ensemble des comparaisons : aucune colonne
    comparée n'est absente d'une comparaison, aucune comparaison ne consomme
    une colonne étrangère au registre.
    """
    colonnes_consommees = {
        colonne for comparaison in COMPARAISONS.values() for colonne in comparaison.colonnes
    }
    assert len(CHAMPS_COMPARES) == len(colonnes_consommees)


def test_ecart_compares_comparaisons_egale_colonnes_en_surplus_des_composites():
    """L'écart entre le nombre de colonnes comparées et le nombre de
    comparaisons égale le nombre de colonnes en surplus dans les
    comparaisons composites (une comparaison à N colonnes compte pour
    N-1 colonnes « en trop » par rapport à une comparaison par colonne).
    """
    surplus = sum(len(comparaison.colonnes) - 1 for comparaison in COMPARAISONS.values())
    assert len(CHAMPS_COMPARES) - len(COMPARAISONS) == surplus


def test_toute_colonne_consommee_figure_parmi_les_colonnes_comparees():
    for comparaison in COMPARAISONS.values():
        for colonne in comparaison.colonnes:
            assert colonne in CHAMPS_COMPARES, (
                f"la comparaison {comparaison.nom!r} consomme la colonne "
                f"{colonne!r}, absente de CHAMPS_COMPARES"
            )


def test_colonnes_comparees_et_colonnes_ecartees_sont_disjointes():
    retenues = set(CHAMPS_COMPARES.keys())
    ecartees = set(COLONNES_ECARTEES.keys())
    assert retenues.isdisjoint(ecartees)


def test_toute_comparaison_porte_une_justification_non_vide():
    for comparaison in COMPARAISONS.values():
        assert comparaison.justification, (
            f"la comparaison {comparaison.nom!r} n'a pas de justification"
        )
        assert comparaison.justification.strip(), (
            f"la comparaison {comparaison.nom!r} a une justification vide de contenu"
        )
