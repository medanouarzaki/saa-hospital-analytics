"""Comparaisons du modèle de rapprochement (linkage.champs.COMPARAISONS).

Ce module N'ESTIME AUCUN PARAMÈTRE et n'exécute aucune prédiction : il
construit les objets de comparaison splink, un par comparaison déclarée
dans le registre, et assemble les paramètres complets (`SettingsCreator`).
L'estimation des paramètres du modèle et la prédiction sont traitées à
part, ailleurs.

Chaque comparaison dérive le ou les noms de colonnes qu'elle consomme du
registre (`linkage.champs.COMPARAISONS`), via `linkage.blocage.colonne_blocage`
— jamais une liste recopiée à la main. Les niveaux vont du plus strict au
plus permissif, se terminent par un niveau par défaut, et les seuils
mesurés fixent l'échelle.
"""

from splink import ColumnExpression
from splink.comparison_level_library import (
    AbsoluteDateDifferenceLevel as _AbsoluteDateDifferenceLevel,
)
from splink.comparison_level_library import (
    CustomLevel,
    DamerauLevenshteinLevel,
    ElseLevel,
    ExactMatchLevel,
    JaroWinklerLevel,
    NullLevel,
)
from splink.comparison_library import CustomComparison

from linkage.blocage import colonne_blocage
from linkage.champs import COMPARAISONS


def comparaison_nom() -> CustomComparison:
    col = colonne_blocage("nom")
    return CustomComparison(
        output_column_name="nom",
        comparison_levels=[
            ExactMatchLevel(col),
            JaroWinklerLevel(col, distance_threshold=0.92),
            JaroWinklerLevel(col, distance_threshold=0.85),
            ElseLevel(),
        ],
    )


def comparaison_nom_famille_1() -> CustomComparison:
    col = colonne_blocage("nom_famille_1")
    return CustomComparison(
        output_column_name="nom_famille_1",
        comparison_levels=[ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_nom_famille_2() -> CustomComparison:
    col = colonne_blocage("nom_famille_2")
    return CustomComparison(
        output_column_name="nom_famille_2",
        comparison_levels=[NullLevel(col), ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_date_naissance(
    ordre_niveaux: list[str] | None = None,
) -> CustomComparison:
    """Comparaison de date_naissance : exact, puis deux niveaux (écart de
    jours, distance de chaîne) dont l'ORDRE a été établi par mesure sur les
    paires vraies et un échantillon de paires arbitraires (l'écart de
    jours s'est révélé nettement plus discriminant que la distance de
    chaîne), puis un niveau par défaut.

    `ordre_niveaux`, si fourni, est la liste ["jours", "chaine"] ou
    ["chaine", "jours"] ; par défaut, l'ordre retenu par cette mesure est
    câblé ici.
    """
    col = "date_naissance"  # colonne brute : Normalisation.AUCUNE, pas de _norm
    col_texte = ColumnExpression(col).cast_to_string()

    niveau_jours = _AbsoluteDateDifferenceLevel(
        col, input_is_string=False, threshold=31, metric="day"
    )
    niveau_chaine = DamerauLevenshteinLevel(col_texte, distance_threshold=4)

    ordre = ordre_niveaux or ["jours", "chaine"]
    niveaux_par_nom = {"jours": niveau_jours, "chaine": niveau_chaine}

    return CustomComparison(
        output_column_name="date_naissance",
        comparison_levels=[
            ExactMatchLevel(col),
            niveaux_par_nom[ordre[0]],
            niveaux_par_nom[ordre[1]],
            ElseLevel(),
        ],
    )


def comparaison_piece_identite() -> CustomComparison:
    """Comparaison composite sur les deux colonnes de la pièce d'identité
    (type ET numéro) : un seul niveau de correspondance exacte porte sur le
    COUPLE des deux colonnes à la fois (voir linkage.champs.COMPARAISONS,
    la comparaison composite), pas deux comparaisons séparées.
    """
    type_col = colonne_blocage("type_piece_identite")
    numero_col = colonne_blocage("n_piece_identite")
    return CustomComparison(
        output_column_name="piece_identite",
        comparison_levels=[
            CustomLevel(
                sql_condition=(
                    f'"{type_col}_l" is null or "{numero_col}_l" is null '
                    f'or "{type_col}_r" is null or "{numero_col}_r" is null'
                ),
                label_for_charts="manquant d'au moins un côté",
            ),
            CustomLevel(
                sql_condition=(
                    f'"{type_col}_l" = "{type_col}_r" and "{numero_col}_l" = "{numero_col}_r"'
                ),
                label_for_charts="correspondance exacte du couple",
            ),
            ElseLevel(),
        ],
    )


def comparaison_telephone_1() -> CustomComparison:
    col = colonne_blocage("telephone_1")
    return CustomComparison(
        output_column_name="telephone_1",
        comparison_levels=[ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_adresse() -> CustomComparison:
    col = colonne_blocage("adresse")
    return CustomComparison(
        output_column_name="adresse",
        comparison_levels=[ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_email() -> CustomComparison:
    col = colonne_blocage("email")
    return CustomComparison(
        output_column_name="email",
        comparison_levels=[NullLevel(col), ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_nom_pere() -> CustomComparison:
    col = colonne_blocage("nom_pere")
    return CustomComparison(
        output_column_name="nom_pere",
        comparison_levels=[ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_nom_mere() -> CustomComparison:
    col = colonne_blocage("nom_mere")
    return CustomComparison(
        output_column_name="nom_mere",
        comparison_levels=[ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_quartier() -> CustomComparison:
    col = colonne_blocage("quartier")
    return CustomComparison(
        output_column_name="quartier",
        comparison_levels=[NullLevel(col), ExactMatchLevel(col), ElseLevel()],
    )


def comparaison_ville() -> CustomComparison:
    """Correspondance exacte AVEC AJUSTEMENT DE FRÉQUENCE : un accord sur
    une valeur rare porte 17 à 36 fois l'information d'un accord sur la
    valeur modale (mesure du registre) ; sans cet ajustement, le champ
    porterait presque aucune information.
    """
    col = colonne_blocage("ville")
    return CustomComparison(
        output_column_name="ville",
        comparison_levels=[
            ExactMatchLevel(col, term_frequency_adjustments=True),
            ElseLevel(),
        ],
    )


def comparaisons(ordre_niveaux_date: list[str] | None = None) -> list[CustomComparison]:
    """Les douze comparaisons, dans l'ordre du registre
    (`linkage.champs.COMPARAISONS`) : une fonction par comparaison, jamais
    une liste recopiée séparément du registre.
    """
    constructeurs = {
        "nom": comparaison_nom,
        "nom_famille_1": comparaison_nom_famille_1,
        "nom_famille_2": comparaison_nom_famille_2,
        "date_naissance": lambda: comparaison_date_naissance(ordre_niveaux_date),
        "telephone_1": comparaison_telephone_1,
        "adresse": comparaison_adresse,
        "email": comparaison_email,
        "nom_pere": comparaison_nom_pere,
        "nom_mere": comparaison_nom_mere,
        "quartier": comparaison_quartier,
        "ville": comparaison_ville,
        "piece_identite": comparaison_piece_identite,
    }
    assert set(constructeurs.keys()) == set(COMPARAISONS.keys()), (
        "les comparaisons construites ici divergent du registre"
    )
    return [constructeurs[nom]() for nom in COMPARAISONS]
