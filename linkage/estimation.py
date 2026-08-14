"""Estimation des paramètres du modèle de rapprochement (linkage.modele).

Ce module N'UTILISE JAMAIS LA VÉRITÉ TERRAIN comme entrée d'un paramètre :
aucune valeur du fichier de vérité terrain n'entre dans un calcul
d'estimation, directement ou via un taux mesuré dessus. La vérité terrain
sert uniquement à JUGER les estimations, après coup — jamais à les
produire ni à les ajuster.

Ce module N'EXÉCUTE AUCUNE PRÉDICTION et n'écrit aucune ligne dans les
tables du schéma linkage : la prédiction est traitée à part, ailleurs.
"""

from pathlib import Path

from splink import Linker, SettingsCreator
from splink.backends.duckdb import DuckDBAPI

from linkage.blocage import (
    colonne_blocage,
    regle_parents_date_naissance,
    regle_piece_identite,
    regles_blocage,
)
from linkage.modele import comparaisons

COLONNE_VILLE = colonne_blocage("ville")
PREFIXE_FREQUENCE = "tf_"

# Règle déterministe utilisée pour estimer la probabilité a priori : la
# plus stricte des quatre règles de blocage, correspondance exacte sur le
# couple (type, numéro) de pièce d'identité.
REGLE_DETERMINISTE_PROBABILITE_A_PRIORI = regle_piece_identite
RAPPEL_HYPOTHESE_PROBABILITE_A_PRIORI = 0.6

# Graine et taille d'échantillon pour l'estimation de u : la plus petite
# valeur de u attendue est celle de la comparaison composite pièce
# d'identité (de l'ordre de 1e-6) ; 1e7 paires donne une espérance
# d'accords suffisante pour ne pas retomber à zéro par malchance
# d'échantillonnage.
GRAINE_ECHANTILLONNAGE_U = 42
TAILLE_ECHANTILLON_U = 1e7

# Couverture minimale pour l'estimation de m par maximisation de
# l'espérance : deux sessions suffisent, aucune comparaison n'étant exclue
# des deux règles à la fois (voir le tableau de couverture, mesuré avant
# tout lancement).
REGLES_SESSIONS_EM = [regle_piece_identite, regle_parents_date_naissance]

CHEMIN_MODELE_ESTIME = Path(__file__).resolve().parent / "modele_estime.json"


def table_frequence_ville(population: list[dict]) -> list[dict]:
    """Table de fréquence de la ville, dans la forme exacte exigée par
    `linker.table_management.register_term_frequency_lookup` : une ligne
    par valeur distincte, colonne de la valeur ET colonne `tf_<colonne>`
    portant une PROPORTION (pas un compte), calculée sur les valeurs non
    manquantes de la population fournie.
    """
    valeurs = [enregistrement[COLONNE_VILLE] for enregistrement in population]
    valeurs_non_manquantes = [v for v in valeurs if v is not None]
    total = len(valeurs_non_manquantes)

    comptes: dict[str, int] = {}
    for valeur in valeurs_non_manquantes:
        comptes[valeur] = comptes.get(valeur, 0) + 1

    colonne_frequence = f"{PREFIXE_FREQUENCE}{COLONNE_VILLE}"
    return [
        {COLONNE_VILLE: valeur, colonne_frequence: compte / total}
        for valeur, compte in comptes.items()
    ]


def construire_linker(population: list[dict]) -> Linker:
    """Construit le Linker sur la population fournie, avec les douze
    comparaisons et les quatre règles de blocage du modèle. N'estime aucun
    paramètre : les paramètres du modèle restent à leurs valeurs par
    défaut tant qu'aucune méthode d'estimation n'a été appelée dessus.
    """
    import pandas as pd

    settings = SettingsCreator(
        link_type="dedupe_only",
        comparisons=comparaisons(),
        blocking_rules_to_generate_predictions=regles_blocage(),
        unique_id_column_name="n_ipp",
    )
    df = pd.DataFrame(population)
    return Linker(df, settings, DuckDBAPI())


def enregistrer_table_frequence_ville(linker: Linker, population: list[dict]) -> None:
    """Construit et enregistre la table de fréquence de la ville auprès du
    linker, condition nécessaire pour que l'ajustement de fréquence déclaré
    sur cette comparaison (linkage.modele.comparaison_ville) ait un effet
    sur le facteur de Bayes.
    """
    table = table_frequence_ville(population)
    linker.table_management.register_term_frequency_lookup(table, COLONNE_VILLE)


def estimer_modele(population: list[dict]) -> Linker:
    """Pipeline complet d'estimation, sans aucune valeur de vérité terrain
    en entrée : table de fréquence de la ville, probabilité a priori
    (règle déterministe + hypothèse de rappel DÉCLARÉE, jamais mesurée sur
    la vérité terrain), u par échantillonnage aléatoire, m par deux
    sessions de maximisation de l'espérance couvrant les douze
    comparaisons. N'exécute aucune prédiction, n'écrit aucune ligne dans
    les tables du schéma linkage.
    """
    linker = construire_linker(population)
    enregistrer_table_frequence_ville(linker, population)

    linker.training.estimate_probability_two_random_records_match(
        [REGLE_DETERMINISTE_PROBABILITE_A_PRIORI()],
        recall=RAPPEL_HYPOTHESE_PROBABILITE_A_PRIORI,
    )
    linker.training.estimate_u_using_random_sampling(
        max_pairs=TAILLE_ECHANTILLON_U, seed=GRAINE_ECHANTILLONNAGE_U
    )
    for regle in REGLES_SESSIONS_EM:
        linker.training.estimate_parameters_using_expectation_maximisation(regle())

    return linker


def sauvegarder_modele(linker: Linker, chemin: Path = CHEMIN_MODELE_ESTIME) -> dict:
    """Sauvegarde le modèle estimé au format JSON de la bibliothèque."""
    return linker.misc.save_model_to_json(str(chemin), overwrite=True)
