"""Règles de blocage pour le rapprochement de patients.

Les quatre règles sont fixées par mesure et ne sont pas rediscutées ici :
  - pièce d'identité : type ET numéro ;
  - premier nom de famille ET téléphone ;
  - premier nom de famille ET adresse ;
  - nom du père ET nom de la mère ET date de naissance.

Toutes portent sur les colonnes NORMALISÉES déclarées dans le registre. La
colonne normalisée d'un champ sans normalisation (`Normalisation.AUCUNE`,
le cas de `date_naissance`) est sa colonne brute elle-même : aucune colonne
"_norm" distincte n'est produite pour ce champ par
`linkage.population.extraire_population` (voir `linkage/champs.py` et
`linkage/population.py`) — bloquer sur sa "forme normalisée" revient alors
à bloquer sur la colonne brute, ce n'est pas une exception à la règle mais
sa conséquence directe.

L'union des quatre règles atteint le rappel maximal mesuré (5 014 paires) ;
la meilleure union à trois règles atteignant ce même rappel coûtait
399 733 paires — un rapport de quatre-vingts qui justifie la quatrième
règle et l'écart par rapport au périmètre initialement prévu à trois
règles.
"""

from splink import block_on
from splink.internals.blocking_rule_creator import BlockingRuleCreator

from linkage.champs import CHAMPS_COMPARES, Normalisation


def colonne_blocage(nom_champ: str) -> str:
    """Nom de colonne à utiliser pour le blocage sur ce champ : sa colonne
    normalisée si le registre en déclare une, sa colonne brute sinon (champ
    sans normalisation, où la colonne brute EST la forme normalisée).
    """
    champ = CHAMPS_COMPARES[nom_champ]
    if champ.normalisation is Normalisation.AUCUNE:
        return nom_champ
    return f"{nom_champ}_norm"


def regle_piece_identite() -> BlockingRuleCreator:
    return block_on(colonne_blocage("type_piece_identite"), colonne_blocage("n_piece_identite"))


def regle_nom_famille_telephone() -> BlockingRuleCreator:
    return block_on(colonne_blocage("nom_famille_1"), colonne_blocage("telephone_1"))


def regle_nom_famille_adresse() -> BlockingRuleCreator:
    return block_on(colonne_blocage("nom_famille_1"), colonne_blocage("adresse"))


def regle_parents_date_naissance() -> BlockingRuleCreator:
    return block_on(
        colonne_blocage("nom_pere"),
        colonne_blocage("nom_mere"),
        colonne_blocage("date_naissance"),
    )


def regles_blocage() -> list[BlockingRuleCreator]:
    """Les quatre règles de blocage retenues pour la prédiction, dans
    l'ordre où elles ont été mesurées.
    """
    return [
        regle_piece_identite(),
        regle_nom_famille_telephone(),
        regle_nom_famille_adresse(),
        regle_parents_date_naissance(),
    ]
