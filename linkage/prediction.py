"""Prédiction : note chaque paire candidate produite par les règles de
blocage, à partir du modèle estimé et persisté.

Ce module ne réestime JAMAIS le modèle : il recharge
`linkage/modele_estime.json` tel quel. Le rechargement PERD la table de
fréquence de la ville (mesuré : deux enregistrements comparés à la main,
l'un concordant sur la valeur modale, l'autre sur la valeur rare, obtiennent
exactement le même poids de correspondance sans réenregistrement — l'écart
n'apparaît qu'après réenregistrement) : elle est donc reconstruite et
réenregistrée après chaque rechargement, jamais supposée conservée.

Aucun seuil n'est appliqué : chaque paire produite par le blocage reçoit un
score, aucune n'est filtrée — le balayage de seuils est traité à part,
ailleurs.
"""

import pandas as pd
from splink import Linker
from splink.backends.duckdb import DuckDBAPI
from splink.internals.splink_dataframe import SplinkDataFrame

from linkage.champs import COMPARAISONS
from linkage.estimation import CHEMIN_MODELE_ESTIME, COLONNE_VILLE, table_frequence_ville
from linkage.population import _connexion, extraire_population

# Le nom de chaque comparaison, dans l'ordre où les fonctions de règle sont
# assemblées par linkage.blocage.regles_blocage() : c'est cet ordre que
# splink numérote via match_key (0 pour la première règle de la liste, et
# ainsi de suite), pas un ordre recopié séparément.
_NOMS_REGLES_DANS_L_ORDRE = (
    "piece_identite",
    "nom_famille_telephone",
    "nom_famille_adresse",
    "parents_date_naissance",
)


def construire_linker_pour_prediction(population: list[dict]) -> Linker:
    """Recharge le modèle persisté (jamais une réestimation) sur la
    population fournie, et réenregistre la table de fréquence de la ville,
    perdue par le rechargement.
    """
    df = pd.DataFrame(population)
    linker = Linker(df, str(CHEMIN_MODELE_ESTIME), DuckDBAPI())
    linker.table_management.register_term_frequency_lookup(
        table_frequence_ville(population), COLONNE_VILLE
    )
    return linker


def predire(population: list[dict] | None = None) -> tuple[SplinkDataFrame, list[dict]]:
    """Note toutes les paires candidates produites par les règles de
    blocage du modèle, sans filtre de seuil. Retourne le résultat splink
    (pas encore transformé en lignes de table) et la population utilisée.
    """
    if population is None:
        population = extraire_population()
    linker = construire_linker_pour_prediction(population)
    resultat = linker.inference.predict()
    return resultat, population


def _ordre_canonique(n_ipp_l: str, n_ipp_r: str) -> tuple[str, str]:
    """Renvoie (n_ipp_1, n_ipp_2) dans l'ordre canonique exigé par la
    contrainte de la table (le premier strictement inférieur au second).
    Mesuré : les paires produites par splink sont déjà toutes
    dans cet ordre pour ce modèle (link_type dedupe_only impose l.n_ipp <
    r.n_ipp dans sa condition de jointure) ; cette fonction reste la
    normalisation défensive écrite au moment de l'écriture, pas une
    supposition.
    """
    return (n_ipp_l, n_ipp_r) if n_ipp_l < n_ipp_r else (n_ipp_r, n_ipp_l)


def lignes_a_inserer(pdf: pd.DataFrame) -> list[tuple]:
    """Construit les lignes prêtes pour l'insertion dans
    linkage.paires_candidates : identifiants dans l'ordre canonique,
    probabilité, poids, un niveau par comparaison du registre (dans l'ordre
    du registre), et le nom de la règle de blocage qui a produit la paire
    (déduit de `match_key`, l'index de la première règle de
    `regles_blocage()` qui a produit cette paire).

    Aucune colonne brute ou normalisée _l/_r n'est conservée dans la table
    cible (seulement les identifiants et les niveaux, symétriques par
    construction) : l'échange de n_ipp_1/n_ipp_2 n'a donc aucune autre
    colonne asymétrique à faire suivre.
    """
    lignes = []
    for ligne in pdf.itertuples(index=False):
        d = ligne._asdict()
        n_ipp_1, n_ipp_2 = _ordre_canonique(d["n_ipp_l"], d["n_ipp_r"])
        regle = _NOMS_REGLES_DANS_L_ORDRE[int(d["match_key"])]
        niveaux = tuple(int(d[f"gamma_{nom}"]) for nom in COMPARAISONS)
        lignes.append(
            (
                n_ipp_1,
                n_ipp_2,
                float(d["match_probability"]),
                float(d["match_weight"]),
                *niveaux,
                regle,
            )
        )
    return lignes


def charger_paires_candidates(pdf: pd.DataFrame, environ: dict[str, str] | None = None) -> int:
    """Vide puis recharge linkage.paires_candidates avec les lignes de
    `pdf` (le résultat de `predire()`), dans une transaction unique —
    idempotent : deux exécutions successives laissent la table dans le
    même état.
    """
    lignes = lignes_a_inserer(pdf)
    noms_colonnes = (
        "n_ipp_1, n_ipp_2, probabilite, poids_correspondance, "
        + ", ".join(f"niveau_{nom}" for nom in COMPARAISONS)
        + ", regle_blocage"
    )
    marqueurs = ", ".join(["%s"] * (5 + len(COMPARAISONS)))
    with _connexion(environ) as connexion, connexion.cursor() as curseur:
        curseur.execute("truncate table linkage.paires_candidates")
        curseur.executemany(
            f"insert into linkage.paires_candidates ({noms_colonnes}) values ({marqueurs})",
            lignes,
        )
        connexion.commit()
    return len(lignes)


def main() -> None:
    resultat, _ = predire()
    pdf = resultat.as_pandas_dataframe()
    nb = charger_paires_candidates(pdf)
    print(f"linkage.paires_candidates : {nb} ligne(s) écrite(s)")


if __name__ == "__main__":
    main()
