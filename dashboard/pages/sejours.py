"""Page des séjours : les cinq indicateurs que le registre déclare pour elle.

C'est la première page dont tous les indicateurs ne répondent pas au filtre de période : un est
filtrable, deux le sont sous réserve, deux ne le sont pas. Chacun porte donc à l'écran ce que le
registre en dit, faute de quoi un lecteur lirait un taux d'occupation annuel comme s'il portait sur
le trimestre qu'il vient de choisir.

Quatre grandeurs réglementaires dépendent de valeurs qui n'existent pas dans les données observées
— la capacité litière, la durée de l'année de référence, la durée de la période couverte : elles
vivent dans la table de paramètres de l'instantané, chacune avec le fichier et la clé d'où elle est
tirée. **Les valeurs et leur provenance s'affichent toutes**, sous une forme qu'un lecteur puisse
aller vérifier. Un taux d'occupation affiché sans dire sur quelle capacité il est calculé n'est pas
un indicateur, c'est un nombre.

Ces quatre grandeurs sont annualisées, et elles emploient la même convention de comptage que les
indicateurs recalculés sur la couche modélisée : une seule convention, donc un seul contrôle
possible pour l'écran et pour l'entrepôt. Deux conventions pour un même indicateur, c'est deux
chiffres différents qu'aucun contrôle ne peut départager.

La durée de séjour s'affiche en distribution et non en moyenne : une moyenne seule ne dit rien
d'une distribution dont la queue porte l'essentiel de la charge en lits.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "sejours"

PARAMETRE_CAPACITE = "capacite_litiere_fonctionnelle"
PARAMETRE_JOURS_ANNEE = "jours_annee_reference"
PARAMETRE_JOURS_PERIODE = "nombre_jours_periode"

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
    # volume ANNUALISÉ à une capacité et à une année de référence, et n'ont de sens qu'ainsi.
    # Aucune clause de période ne leur est appliquée, ce que le registre déclare et que l'écran
    # répète.
    #
    # La convention de comptage est celle des indicateurs recalculés sur la couche modélisée, et
    # non une seconde qui lui serait propre. Trois traits la définissent, et chacun a une raison :
    #
    #   - la durée d'un séjour est mesurée sur ses HORODATAGES, pas sur la différence de ses dates ;
    #   - un séjour non clos n'est pas exclu mais CENSURÉ à la date de référence des données, celle
    #     que porte la table d'état : l'exclure retirerait ses journées du numérateur tout en
    #     laissant son admission au dénominateur, et la durée moyenne mêlerait alors deux
    #     populations ;
    #   - les deux volumes sont ANNUALISÉS par le rapport de l'année de référence à la durée de la
    #     période couverte, faute de quoi un taux de rotation lu sur deux ans et demi serait comparé
    #     à un taux annuel publié.
    #
    # La durée employée pour annualiser est celle que la configuration DÉCLARE, et non l'étendue
    # observée des faits : les deux diffèrent d'un jour ici — aucune admission ne tombe le premier
    # jour de la période — et cet écart d'un seul jour déplace le taux d'occupation de 0,0586 point,
    # mesuré. Annualiser sur l'étendue observée ferait donc dépendre un indicateur publié du hasard
    # de la première admission.
    #
    # Les quatre valeurs qui entrent ici — capacité, année de référence, durée de la période et
    # borne de censure — sont LUES, jamais écrites : les trois premières dans la table de paramètres
    # avec leur provenance, la dernière dans la table d'état. Une seule d'entre elles écrite en
    # clair suffirait à faire diverger l'écran de la configuration sans que rien ne le signale.
    "sejours_indicateurs_reglementaires": """
        with bornes as (
            select min(jour_admission) as debut,
                   max(coalesce(jour_sortie, jour_admission)) as fin,
                   (select max(date_reference_donnees) from instantane_etat) as censure
            from fct_sejour
        ),
        mesures as (
            select count(*) as sejours,
                   sum(
                       extract(
                           epoch from (
                               coalesce(
                                   date_heure_sortie,
                                   ((select censure from bornes) + time '23:59:59')
                                       at time zone 'UTC'
                               ) - date_heure_admission
                           )
                       ) / 86400.0
                   ) as journees,
                   (select fin - debut + 1 from bornes) as jours_periode
            from fct_sejour
        ),
        annualisees as (
            select sejours, journees, jours_periode,
                   journees * %(jours_annee)s / %(jours_periode)s as journees_annuelles,
                   sejours::numeric * %(jours_annee)s / %(jours_periode)s as sejours_annuels
            from mesures
        )
        select sejours, journees, jours_periode,
               journees_annuelles / (%(jours_annee)s * %(capacite)s) as taux_occupation,
               journees_annuelles / sejours_annuels as duree_moyenne_jours,
               sejours_annuels / %(capacite)s as rotation,
               (%(jours_annee)s * %(capacite)s - journees_annuelles) / sejours_annuels
                   as intervalle_rotation_jours
        from annualisees
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


def _parametre(nom: str) -> dict:
    """Un paramètre et sa provenance, lus dans la table de paramètres.

    Rien n'est écrit en dur : la valeur, le fichier et la clé viennent tous de la même ligne, ce
    qui rend la provenance affichée vérifiable plutôt que décorative. L'absence lève plutôt que de
    rendre une valeur de repli : un indicateur calculé sur une capacité par défaut serait faux sans
    que rien ne le dise.
    """
    parametres = lecture.interroger(
        "select nom, valeur, provenance_fichier, provenance_cle from instantane_parametres "
        f"where nom = '{nom}'"
    )
    if parametres.empty:
        raise KeyError(f"paramètre absent de l'instantané : {nom}")
    return parametres.iloc[0].to_dict()


def _capacite() -> dict:
    """La capacité litière et sa provenance. Conservée sous ce nom : elle est affichée à part."""
    return _parametre(PARAMETRE_CAPACITE)


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
    rendu.tracer_temporel(
        rendu.en_nombres(mensuel, "journees"),
        x="mois",
        y=["admissions", "journees"],
        x_label="Mois d'admission",
        y_label="Effectif",
        forme="bar",
    )

    rendu.titre_indicateur("sejours_indicateurs_reglementaires")
    jours_annee = _parametre(PARAMETRE_JOURS_ANNEE)
    jours_periode = _parametre(PARAMETRE_JOURS_PERIODE)
    reglementaires = q(
        "sejours_indicateurs_reglementaires",
        capacite=int(capacite["valeur"]),
        jours_annee=int(jours_annee["valeur"]),
        jours_periode=int(jours_periode["valeur"]),
    )
    ligne = reglementaires.iloc[0]
    st.caption(
        f"Grandeurs **annualisées** : les volumes observés sur les "
        f"{int(jours_periode['valeur'])} jours de la période sont ramenés à une année de "
        f"{int(jours_annee['valeur'])} jours, puis rapportés à une capacité litière de "
        f"**{capacite['valeur']} lits**. Un séjour non clos n'est pas écarté : sa durée "
        f"est arrêtée à la date de référence des données. "
        f"Aucune de ces valeurs ne figure dans les données observées ; elles sont lues dans "
        f"`{capacite['provenance_fichier']}`, clé `{capacite['provenance_cle']}`, et dans "
        f"`{jours_annee['provenance_fichier']}`, clés `{jours_annee['provenance_cle']}` et "
        f"`{jours_periode['provenance_cle']}`. "
        f"Étendue observée des faits : {int(ligne['jours_periode'])} jours."
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
