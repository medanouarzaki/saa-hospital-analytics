"""Page des séjours : les cinq indicateurs que le registre déclare pour elle.

C'est la première page dont tous les indicateurs ne répondent pas au filtre de période : un est
filtrable, deux le sont sous réserve, deux ne le sont pas. Chacun porte donc à l'écran ce que le
registre en dit, faute de quoi un lecteur lirait un taux d'occupation annuel comme s'il portait sur
le trimestre qu'il vient de choisir.

Quatre grandeurs réglementaires dépendent de la capacité litière, qui n'existe pas dans les données
observées : elle vit dans la table de paramètres de l'instantané, avec le fichier et la clé d'où
elle est tirée. **La valeur et sa provenance s'affichent toutes deux**, sous une forme qu'un lecteur
puisse aller vérifier. Un taux d'occupation affiché sans dire sur quelle capacité il est calculé
n'est pas un indicateur, c'est un nombre.

La durée de séjour s'affiche en distribution et non en moyenne : une moyenne seule ne dit rien
d'une distribution dont la queue porte l'essentiel de la charge en lits.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "sejours"

PARAMETRE_CAPACITE = "capacite_litiere_fonctionnelle"

REQUETES = {
    "sejours_admissions_journees": """
        select date_trunc('month', jour_admission)::date as mois,
               count(*) as admissions,
               sum(duree_jours) as journees
        from fct_sejour
        {filtre}
        group by date_trunc('month', jour_admission)
        order by mois
    """,
    # Les quatre grandeurs réglementaires portent sur la période complète : elles rapportent un
    # volume à une capacité et à un nombre de jours, et n'ont de sens qu'ainsi. Aucune clause de
    # période ne leur est appliquée, ce que le registre déclare et que l'écran répète.
    "sejours_indicateurs_reglementaires": """
        with bornes as (
            select min(jour_admission) as debut,
                   max(coalesce(jour_sortie, jour_admission)) as fin
            from fct_sejour
        ),
        mesures as (
            select count(*) as sejours,
                   sum(duree_jours) as journees,
                   (select fin - debut + 1 from bornes) as jours_periode
            from fct_sejour
        )
        select sejours, journees, jours_periode,
               journees::numeric / (jours_periode * %(capacite)s) as taux_occupation,
               journees::numeric / sejours as duree_moyenne_jours,
               sejours::numeric / %(capacite)s as rotation,
               (jours_periode * %(capacite)s - journees)::numeric / sejours
                   as intervalle_rotation_jours
        from mesures
    """,
    "sejours_repartition_service": """
        select service_accueil,
               count(*) as sejours,
               count(*)::numeric / sum(count(*)) over () as part
        from fct_sejour
        {filtre}
        group by service_accueil
        order by service_accueil
    """,
    # Le décompte affiché est celui des séjours DONT LA DURÉE EST CONNUE, non celui de tous les
    # séjours : les séjours non clos n'en ont pas, et les centiles les ignorent. Annoncer le
    # décompte total à côté d'une distribution calculée sans eux ferait lire l'un pour l'autre.
    "sejours_distribution_duree": """
        select count(duree_jours) as sejours_avec_duree,
               count(*) - count(duree_jours) as sejours_sans_duree,
               min(duree_jours) as minimum,
               percentile_cont(0.25) within group (order by duree_jours) as premier_quartile,
               percentile_cont(0.5) within group (order by duree_jours) as mediane,
               percentile_cont(0.75) within group (order by duree_jours) as troisieme_quartile,
               percentile_cont(0.9) within group (order by duree_jours) as p90_jours,
               max(duree_jours) as maximum
        from fct_sejour
        {filtre}
    """,
    # L'ancienneté se compte depuis la date de référence des données, jamais depuis l'horloge :
    # quarante-six jours les séparent, et compter depuis l'horloge vieillirait tous les séjours
    # d'autant.
    "sejours_non_clos": """
        select count(*) as sejours,
               count(*) filter (where not est_clos) as non_clos,
               count(*) filter (where not est_clos)::numeric / count(*) as part,
               (select max(date_reference_donnees) from instantane_etat)
                   - min(jour_admission) filter (where not est_clos) as anciennete_jours
        from fct_sejour
    """,
}


def _capacite() -> dict:
    """La capacité litière et sa provenance, lues dans la table de paramètres.

    Rien n'est écrit en dur : la valeur, le fichier et la clé viennent tous de la même ligne, ce
    qui rend la provenance affichée vérifiable plutôt que décorative.
    """
    parametres = lecture.interroger(
        "select nom, valeur, provenance_fichier, provenance_cle from instantane_parametres "
        f"where nom = '{PARAMETRE_CAPACITE}'"
    )
    if parametres.empty:
        raise KeyError(f"paramètre absent de l'instantané : {PARAMETRE_CAPACITE}")
    return parametres.iloc[0].to_dict()


def rendre() -> None:
    rendu.en_tete("Séjours")
    bornes = lecture.interroger(
        "select min(jour_admission) as debut, max(jour_admission) as fin from fct_sejour"
    )
    periode = rendu.filtre_de_page(PAGE, (bornes["debut"][0], bornes["fin"][0]))

    def q(identifiant: str, **parametres):
        requete = REQUETES[identifiant]
        if "{filtre}" in requete:
            requete = requete.format(filtre=rendu.clause_periode(identifiant, periode))
        return lecture.interroger(requete % parametres if parametres else requete)

    capacite = _capacite()

    rendu.titre_indicateur("sejours_admissions_journees")
    mensuel = q("sejours_admissions_journees")
    st.bar_chart(
        mensuel,
        x="mois",
        y=["admissions", "journees"],
        x_label="Mois d'admission",
        y_label="Effectif",
    )

    rendu.titre_indicateur("sejours_indicateurs_reglementaires")
    reglementaires = q("sejours_indicateurs_reglementaires", capacite=int(capacite["valeur"]))
    ligne = reglementaires.iloc[0]
    st.caption(
        f"Calculés sur une capacité litière de **{capacite['valeur']} lits**, valeur qui ne figure "
        f"pas dans les données observées et qui est lue dans "
        f"`{capacite['provenance_fichier']}`, clé `{capacite['provenance_cle']}`. "
        f"Période couverte : {int(ligne['jours_periode'])} jours."
    )
    colonnes = st.columns(4)
    with colonnes[0]:
        taux = f"{100 * float(ligne['taux_occupation']):.1f} %".replace(".", ",")
        st.metric("Taux d'occupation", taux)
    with colonnes[1]:
        duree = f"{float(ligne['duree_moyenne_jours']):.1f} j".replace(".", ",")
        st.metric("Durée moyenne de séjour", duree)
    with colonnes[2]:
        st.metric("Taux de rotation", f"{float(ligne['rotation']):.1f}".replace(".", ","))
    with colonnes[3]:
        st.metric(
            "Intervalle de rotation",
            f"{float(ligne['intervalle_rotation_jours']):.1f} j".replace(".", ","),
        )

    rendu.titre_indicateur("sejours_repartition_service")
    services = q("sejours_repartition_service")
    st.bar_chart(
        services,
        x="service_accueil",
        y="sejours",
        x_label="Service d'accueil",
        y_label="Séjours",
    )
    st.dataframe(services, hide_index=True)
    st.caption(
        "Les codes de service sont affichés tels quels : aucun libellé n'est documenté pour eux, "
        "et aucun n'est inventé ici."
    )

    rendu.titre_indicateur("sejours_distribution_duree")
    distribution = q("sejours_distribution_duree")
    st.dataframe(distribution, hide_index=True)

    rendu.titre_indicateur("sejours_non_clos")
    non_clos = q("sejours_non_clos")
    ligne = non_clos.iloc[0]
    gauche, droite = st.columns(2)
    with gauche:
        st.metric(
            "Séjours non clos",
            f"{int(ligne['non_clos'])} sur {int(ligne['sejours'])}",
            help="Séjours sans date de sortie à la date de référence des données",
        )
    with droite:
        st.metric("Ancienneté du plus ancien", f"{int(ligne['anciennete_jours'])} jours")
    st.caption(
        "L'ancienneté se compte depuis la date de référence des données, et non depuis la date du "
        "jour : ces deux dates ne coïncident pas."
    )


rendre()
