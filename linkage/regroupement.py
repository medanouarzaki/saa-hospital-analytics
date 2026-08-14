"""Regroupement transitif (clustering) et métrique de grappe.

Ne peuple aucune table : le seuil auquel les grappes seront persistées
n'est pas encore décidé, ce sera traité à part, ailleurs. Ce module fournit
la fonction de regroupement et la métrique de grappe ; il ne lit
`linkage.paires_candidates` qu'en LECTURE et n'écrit dans aucune table.
"""

from collections import defaultdict

from linkage.population import _connexion, extraire_population
from linkage.prediction import construire_linker_pour_prediction


def regrouper(seuil_probabilite: float, population: list[dict] | None = None):
    """Regroupe via `linker.clustering.cluster_pairwise_predictions_at_threshold`,
    à un seuil donné, sur une réexécution EN MÉMOIRE de la prédiction (le
    modèle persisté n'est jamais réestimé, `linkage.paires_candidates`
    n'est jamais réécrite). Retourne un dict {n_ipp: cluster_id}.
    """
    if population is None:
        population = extraire_population()
    linker = construire_linker_pour_prediction(population)
    df_predict = linker.inference.predict()
    df_clusters = linker.clustering.cluster_pairwise_predictions_at_threshold(
        df_predict, threshold_match_probability=seuil_probabilite
    )
    pdf = df_clusters.as_pandas_dataframe()
    return dict(zip(pdf["n_ipp"], pdf["cluster_id"], strict=True))


def paires_depuis_la_base(environ: dict[str, str] | None = None) -> list[tuple[str, str, float]]:
    """Lit (n_ipp_1, n_ipp_2, probabilite) depuis linkage.paires_candidates
    — lecture seule, jamais une écriture.
    """
    with _connexion(environ) as connexion, connexion.cursor() as curseur:
        curseur.execute("select n_ipp_1, n_ipp_2, probabilite from linkage.paires_candidates")
        return curseur.fetchall()


def composantes_connexes(
    paires: list[tuple[str, str, float]],
    seuil: float,
    population: list[dict] | None = None,
) -> dict[str, str]:
    """Traversée de composantes connexes écrite à la main (union-find),
    sur une liste de paires (n_ipp_1, n_ipp_2, probabilité), au-dessus du
    seuil donné. Chaque enregistrement de la population, apparié ou non,
    forme son propre singleton au départ — comme le fait la bibliothèque
    (une ligne par enregistrement dans sa sortie, pas seulement pour les
    enregistrements appariés). Retourne un dict {n_ipp: identifiant de
    grappe}.
    """
    if population is None:
        population = extraire_population()

    parent: dict[str, str] = {
        enregistrement["n_ipp"]: enregistrement["n_ipp"] for enregistrement in population
    }

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for n1, n2, probabilite in paires:
        if probabilite >= seuil:
            union(n1, n2)

    return {n_ipp: find(n_ipp) for n_ipp in parent}


def tailles_des_grappes(affectation: dict[str, str]) -> dict[str, int]:
    """{cluster_id: taille}, à partir d'un dict {n_ipp: cluster_id}."""
    compte: dict[str, int] = defaultdict(int)
    for cluster_id in affectation.values():
        compte[cluster_id] += 1
    return dict(compte)


def partition_verite_terrain(
    population: list[dict], paires_verite_terrain_presentes: list[tuple[str, str]]
) -> dict[str, str]:
    """La partition VRAIE : une grappe de deux par paire de vérité terrain
    présente, un singleton pour chaque autre enregistrement de la
    population.
    """
    partition: dict[str, str] = {}
    dans_une_paire: set[str] = set()
    for indice, (n1, n2) in enumerate(paires_verite_terrain_presentes):
        cluster_id = f"vt_{indice}"
        partition[n1] = cluster_id
        partition[n2] = cluster_id
        dans_une_paire.add(n1)
        dans_une_paire.add(n2)

    for enregistrement in population:
        n_ipp = enregistrement["n_ipp"]
        if n_ipp not in dans_une_paire:
            partition[n_ipp] = n_ipp

    return partition


def _groupes(partition: dict[str, str]) -> dict[str, set[str]]:
    groupes: dict[str, set[str]] = defaultdict(set)
    for n_ipp, cluster_id in partition.items():
        groupes[cluster_id].add(n_ipp)
    return dict(groupes)


def metrique_grappe(
    partition_predite: dict[str, str],
    partition_vraie: dict[str, str],
    restreindre_a: set[str] | None = None,
) -> dict[str, int]:
    """Métrique de grappe, sur les deux partitions données (restreintes à
    `restreindre_a` si fourni, sinon sur toute la population commune aux
    deux partitions) :
      - vraies_retrouvees : grappes vraies exactement retrouvées (une
        grappe prédite ne compte que si elle est EXACTEMENT égale à une
        grappe vraie) ;
      - predites_sans_correspondance : grappes prédites de taille > 1 ne
        correspondant EXACTEMENT à aucune grappe vraie ;
      - enregistrements_sur_fusionnes : enregistrements pris dans une
        grappe prédite qui contient des membres de plus d'une grappe
        vraie.
    """
    if restreindre_a is not None:
        partition_predite = {k: v for k, v in partition_predite.items() if k in restreindre_a}
        partition_vraie = {k: v for k, v in partition_vraie.items() if k in restreindre_a}

    groupes_predits = _groupes(partition_predite)
    groupes_vrais = _groupes(partition_vraie)

    sets_vrais = {frozenset(membres) for membres in groupes_vrais.values()}
    sets_predits = {frozenset(membres) for membres in groupes_predits.values()}

    vraies_retrouvees = len(sets_vrais & sets_predits)

    predites_sans_correspondance = sum(
        1 for ensemble in sets_predits if len(ensemble) > 1 and ensemble not in sets_vrais
    )

    enregistrements_sur_fusionnes = 0
    for membres in groupes_predits.values():
        grappes_vraies_touchees = {partition_vraie[m] for m in membres if m in partition_vraie}
        if len(grappes_vraies_touchees) > 1:
            enregistrements_sur_fusionnes += len(membres)

    return {
        "vraies_retrouvees": vraies_retrouvees,
        "predites_sans_correspondance": predites_sans_correspondance,
        "enregistrements_sur_fusionnes": enregistrements_sur_fusionnes,
    }
