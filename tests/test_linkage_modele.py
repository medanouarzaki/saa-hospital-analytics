"""Tests des comparaisons du modèle de rapprochement (linkage.modele).

Aucune base requise : le Linker est construit sur une table en mémoire
dont les colonnes sont dérivées du registre, jamais sur des données
extraites de PostgreSQL. Aucun paramètre n'est estimé, aucune prédiction
n'est lancée sur la population réelle — ce module ne fait qu'assigner un
niveau à des paires construites à la main, une par comparaison et par
niveau, avec le niveau attendu écrit explicitement (ce ne sont pas des
littéraux de volumétrie : ce sont des cas de test explicites, légitimes).

Les bandes de similarité du prénom ont été choisies par mesure préalable
(`rapidfuzz.distance.JaroWinkler.similarity`) : "ahmed benani"/"ahmed
benali" -> 0,967 (bande >=0,92), "ahmed benani"/"ahmad benali" -> 0,876
(bande >=0,85 et <0,92).
"""

import datetime

import pandas as pd
import pytest
from splink import Linker, SettingsCreator
from splink.backends.duckdb import DuckDBAPI

from linkage.blocage import regles_blocage
from linkage.champs import CHAMPS_COMPARES, COMPARAISONS, Normalisation
from linkage.modele import comparaisons

_DATE_GABARIT = datetime.date(1980, 1, 1)


def _colonnes_population() -> list[str]:
    colonnes = ["n_ipp"]
    for nom_champ, champ in CHAMPS_COMPARES.items():
        colonnes.append(nom_champ)
        if champ.normalisation is not Normalisation.AUCUNE:
            colonnes.append(f"{nom_champ}_norm")
    return colonnes


def _gabarit() -> dict:
    gabarit = {colonne: None for colonne in _colonnes_population()}
    gabarit["date_naissance"] = _DATE_GABARIT
    return gabarit


def _enregistrement(n_ipp: str, **valeurs) -> dict:
    enregistrement = dict(_gabarit())
    enregistrement["n_ipp"] = n_ipp
    enregistrement.update(valeurs)
    return enregistrement


@pytest.fixture(scope="module")
def linker() -> Linker:
    table = pd.DataFrame([_enregistrement("GABARIT-1"), _enregistrement("GABARIT-2")])
    settings = SettingsCreator(
        link_type="dedupe_only",
        comparisons=comparaisons(),
        blocking_rules_to_generate_predictions=regles_blocage(),
        unique_id_column_name="n_ipp",
    )
    return Linker(table, settings, DuckDBAPI())


def _niveau(linker: Linker, r1: dict, r2: dict, colonne_gamma: str) -> int:
    resultat = linker.inference.compare_two_records(r1, r2)
    dataframe = resultat.as_pandas_dataframe()
    return int(dataframe[colonne_gamma].iloc[0])


# --- nom : exact, similarité>=0.92, similarité>=0.85, défaut -----------------


def test_nom_exact(linker):
    r1 = _enregistrement("N1", nom_norm="ahmed benani")
    r2 = _enregistrement("N2", nom_norm="ahmed benani")
    assert _niveau(linker, r1, r2, "gamma_nom") == 3


def test_nom_similarite_0_92(linker):
    r1 = _enregistrement("N3", nom_norm="ahmed benani")
    r2 = _enregistrement("N4", nom_norm="ahmed benali")
    assert _niveau(linker, r1, r2, "gamma_nom") == 2


def test_nom_similarite_0_85(linker):
    r1 = _enregistrement("N5", nom_norm="ahmed benani")
    r2 = _enregistrement("N6", nom_norm="ahmad benali")
    assert _niveau(linker, r1, r2, "gamma_nom") == 1


def test_nom_defaut(linker):
    r1 = _enregistrement("N7", nom_norm="ahmed benani")
    r2 = _enregistrement("N8", nom_norm="xxxxxxxxxxxx")
    assert _niveau(linker, r1, r2, "gamma_nom") == 0


# --- nom_famille_1 : exact, défaut -------------------------------------------


def test_nom_famille_1_exact(linker):
    r1 = _enregistrement("O1", nom_famille_1_norm="benani")
    r2 = _enregistrement("O2", nom_famille_1_norm="benani")
    assert _niveau(linker, r1, r2, "gamma_nom_famille_1") == 1


def test_nom_famille_1_defaut(linker):
    r1 = _enregistrement("O3", nom_famille_1_norm="benani")
    r2 = _enregistrement("O4", nom_famille_1_norm="alaoui")
    assert _niveau(linker, r1, r2, "gamma_nom_famille_1") == 0


# --- nom_famille_2 : manquant, exact, défaut ---------------------------------


def test_nom_famille_2_manquant(linker):
    r1 = _enregistrement("P1", nom_famille_2_norm=None)
    r2 = _enregistrement("P2", nom_famille_2_norm=None)
    assert _niveau(linker, r1, r2, "gamma_nom_famille_2") == -1


def test_nom_famille_2_exact(linker):
    r1 = _enregistrement("P3", nom_famille_2_norm="alami")
    r2 = _enregistrement("P4", nom_famille_2_norm="alami")
    assert _niveau(linker, r1, r2, "gamma_nom_famille_2") == 1


def test_nom_famille_2_defaut(linker):
    r1 = _enregistrement("P5", nom_famille_2_norm="alami")
    r2 = _enregistrement("P6", nom_famille_2_norm="idrissi")
    assert _niveau(linker, r1, r2, "gamma_nom_famille_2") == 0


# --- date_naissance : exact, jours<=31, chaîne<=4, défaut --------------------


def test_date_naissance_exact(linker):
    r1 = _enregistrement("Q1", date_naissance=datetime.date(1980, 1, 1))
    r2 = _enregistrement("Q2", date_naissance=datetime.date(1980, 1, 1))
    assert _niveau(linker, r1, r2, "gamma_date_naissance") == 3


def test_date_naissance_jours(linker):
    r1 = _enregistrement("Q3", date_naissance=datetime.date(1980, 1, 1))
    r2 = _enregistrement("Q4", date_naissance=datetime.date(1980, 1, 20))
    assert _niveau(linker, r1, r2, "gamma_date_naissance") == 2


def test_date_naissance_chaine(linker):
    r1 = _enregistrement("Q5", date_naissance=datetime.date(1980, 1, 1))
    r2 = _enregistrement("Q6", date_naissance=datetime.date(1985, 6, 15))
    assert _niveau(linker, r1, r2, "gamma_date_naissance") == 1


def test_date_naissance_defaut(linker):
    r1 = _enregistrement("Q7", date_naissance=datetime.date(1980, 1, 1))
    r2 = _enregistrement("Q8", date_naissance=datetime.date(2010, 11, 23))
    assert _niveau(linker, r1, r2, "gamma_date_naissance") == 0


# --- piece_identite : manquant (>=1 côté), exact (couple), défaut -----------


def test_piece_identite_manquant(linker):
    r1 = _enregistrement("R1", type_piece_identite_norm=None, n_piece_identite_norm=None)
    r2 = _enregistrement("R2", type_piece_identite_norm="cin", n_piece_identite_norm="cin123")
    assert _niveau(linker, r1, r2, "gamma_piece_identite") == 2


def test_piece_identite_exact(linker):
    r1 = _enregistrement("R3", type_piece_identite_norm="cin", n_piece_identite_norm="cin123")
    r2 = _enregistrement("R4", type_piece_identite_norm="cin", n_piece_identite_norm="cin123")
    assert _niveau(linker, r1, r2, "gamma_piece_identite") == 1


def test_piece_identite_defaut(linker):
    r1 = _enregistrement("R5", type_piece_identite_norm="cin", n_piece_identite_norm="cin123")
    r2 = _enregistrement("R6", type_piece_identite_norm="cin", n_piece_identite_norm="cin999")
    assert _niveau(linker, r1, r2, "gamma_piece_identite") == 0


# --- telephone_1 : exact, défaut ---------------------------------------------


def test_telephone_1_exact(linker):
    r1 = _enregistrement("S1", telephone_1_norm="0600000000")
    r2 = _enregistrement("S2", telephone_1_norm="0600000000")
    assert _niveau(linker, r1, r2, "gamma_telephone_1") == 1


def test_telephone_1_defaut(linker):
    r1 = _enregistrement("S3", telephone_1_norm="0600000000")
    r2 = _enregistrement("S4", telephone_1_norm="0611111111")
    assert _niveau(linker, r1, r2, "gamma_telephone_1") == 0


# --- adresse : exact, défaut --------------------------------------------------


def test_adresse_exact(linker):
    r1 = _enregistrement("T1", adresse_norm="12 rue x")
    r2 = _enregistrement("T2", adresse_norm="12 rue x")
    assert _niveau(linker, r1, r2, "gamma_adresse") == 1


def test_adresse_defaut(linker):
    r1 = _enregistrement("T3", adresse_norm="12 rue x")
    r2 = _enregistrement("T4", adresse_norm="45 avenue y")
    assert _niveau(linker, r1, r2, "gamma_adresse") == 0


# --- email : manquant, exact, défaut -----------------------------------------


def test_email_manquant(linker):
    r1 = _enregistrement("U1", email_norm=None)
    r2 = _enregistrement("U2", email_norm=None)
    assert _niveau(linker, r1, r2, "gamma_email") == -1


def test_email_exact(linker):
    r1 = _enregistrement("U3", email_norm="a@x.com")
    r2 = _enregistrement("U4", email_norm="a@x.com")
    assert _niveau(linker, r1, r2, "gamma_email") == 1


def test_email_defaut(linker):
    r1 = _enregistrement("U5", email_norm="a@x.com")
    r2 = _enregistrement("U6", email_norm="b@y.com")
    assert _niveau(linker, r1, r2, "gamma_email") == 0


# --- nom_pere : exact, défaut --------------------------------------------------


def test_nom_pere_exact(linker):
    r1 = _enregistrement("V1", nom_pere_norm="said")
    r2 = _enregistrement("V2", nom_pere_norm="said")
    assert _niveau(linker, r1, r2, "gamma_nom_pere") == 1


def test_nom_pere_defaut(linker):
    r1 = _enregistrement("V3", nom_pere_norm="said")
    r2 = _enregistrement("V4", nom_pere_norm="omar")
    assert _niveau(linker, r1, r2, "gamma_nom_pere") == 0


# --- nom_mere : exact, défaut --------------------------------------------------


def test_nom_mere_exact(linker):
    r1 = _enregistrement("W1", nom_mere_norm="fatima")
    r2 = _enregistrement("W2", nom_mere_norm="fatima")
    assert _niveau(linker, r1, r2, "gamma_nom_mere") == 1


def test_nom_mere_defaut(linker):
    r1 = _enregistrement("W3", nom_mere_norm="fatima")
    r2 = _enregistrement("W4", nom_mere_norm="khadija")
    assert _niveau(linker, r1, r2, "gamma_nom_mere") == 0


# --- quartier : manquant, exact, défaut ---------------------------------------


def test_quartier_manquant(linker):
    r1 = _enregistrement("X1", quartier_norm=None)
    r2 = _enregistrement("X2", quartier_norm=None)
    assert _niveau(linker, r1, r2, "gamma_quartier") == -1


def test_quartier_exact(linker):
    r1 = _enregistrement("X3", quartier_norm="centre")
    r2 = _enregistrement("X4", quartier_norm="centre")
    assert _niveau(linker, r1, r2, "gamma_quartier") == 1


def test_quartier_defaut(linker):
    r1 = _enregistrement("X5", quartier_norm="centre")
    r2 = _enregistrement("X6", quartier_norm="peripherie")
    assert _niveau(linker, r1, r2, "gamma_quartier") == 0


# --- ville : exact (avec ajustement de fréquence), défaut --------------------


def test_ville_exact(linker):
    r1 = _enregistrement("Y1", ville_norm="casablanca")
    r2 = _enregistrement("Y2", ville_norm="casablanca")
    assert _niveau(linker, r1, r2, "gamma_ville") == 1


def test_ville_defaut(linker):
    r1 = _enregistrement("Y3", ville_norm="casablanca")
    r2 = _enregistrement("Y4", ville_norm="rabat")
    assert _niveau(linker, r1, r2, "gamma_ville") == 0


def test_ville_porte_l_ajustement_de_frequence():
    """Propriété structurelle, pas un niveau : la comparaison ville doit
    déclarer term_frequency_adjustments=True sur son niveau de
    correspondance exacte, sans quoi l'ajustement de fréquence mesuré
    ne s'appliquerait jamais.
    """
    comparaison_ville = next(c for c in comparaisons() if c.create_output_column_name() == "ville")
    niveaux = comparaison_ville.create_comparison_levels()
    niveaux_avec_ajustement = [
        n for n in niveaux if getattr(n, "term_frequency_adjustments", False) is True
    ]
    assert niveaux_avec_ajustement, "aucun niveau de 'ville' ne porte l'ajustement de fréquence"


# --- construction paramétrable, réservée à l'étude d'ablation (linkage.ablation) --


def test_comparaisons_par_defaut_identiques_au_modele_complet():
    """Le chemin paramétrable, appelé sans argument, DOIT rester le modèle
    complet du dépôt, mot pour mot : mêmes noms de comparaison, dans le même
    ordre, même compte. Une variante qui modifierait discrètement le modèle
    de référence serait un défaut sérieux et silencieux.
    """
    reference = comparaisons()
    via_chemin_parametrable = comparaisons(
        exclure=frozenset(), neutraliser_absence_piece_identite=False
    )
    assert [c.create_output_column_name() for c in reference] == [
        c.create_output_column_name() for c in via_chemin_parametrable
    ]
    assert len(reference) == len(via_chemin_parametrable) == len(COMPARAISONS) == 12


def test_exclure_retire_exactement_les_comparaisons_demandees():
    a_exclure = frozenset({"quartier", "ville", "nom_pere"})
    resultat = comparaisons(exclure=a_exclure)
    noms_restants = {c.create_output_column_name() for c in resultat}
    assert noms_restants == set(COMPARAISONS.keys()) - a_exclure
    assert len(resultat) == len(COMPARAISONS) - len(a_exclure)


def test_neutraliser_absence_piece_identite_marque_is_null_level():
    """Le niveau d'absence à sens unique, neutralisé, doit porter
    `is_null_level=True` (le mécanisme que la bibliothèque réserve aux
    niveaux de valeur manquante, sans m/u estimés) ; par défaut, ce même
    niveau reste un niveau ordinaire (is_null_level=False).
    """
    pid_neutralise = next(
        c
        for c in comparaisons(neutraliser_absence_piece_identite=True)
        if c.create_output_column_name() == "piece_identite"
    )
    niveaux = pid_neutralise.create_comparison_levels()
    niveau_absence = next(
        n for n in niveaux if n.create_label_for_charts() == "manquant d'au moins un côté"
    )
    assert niveau_absence.is_null_level is True

    pid_defaut = next(
        c for c in comparaisons() if c.create_output_column_name() == "piece_identite"
    )
    niveau_absence_defaut = next(
        n
        for n in pid_defaut.create_comparison_levels()
        if n.create_label_for_charts() == "manquant d'au moins un côté"
    )
    assert niveau_absence_defaut.is_null_level is False
