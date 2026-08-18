"""Page de facturation : les huit indicateurs que le registre déclare pour elle.

Deux taux y coexistent et **ne répondent pas à la même question**. Le taux de recouvrement rapporte
ce qui a été recouvré à ce qui est devenu créance ; le taux d'encaissement rapporte ce qui a été
encaissé à ce qui a été facturé. Une facture sur quatre environ donne lieu à une créance, si bien
que les deux dénominateurs n'ont ni la même taille ni le même sens, et que les deux taux prennent
des valeurs très éloignées.

**Ils sont donc affichés côte à côte, jamais l'un sans l'autre**, chacun avec sa définition et avec
la phrase qui dit ce qu'il rapporte à quoi. Un écran qui n'en montrerait qu'un laisserait conclure
soit que presque rien ne rentre, soit que presque tout rentre, selon celui qu'on aurait retenu.

L'ancienneté des créances se compte depuis la date de référence des données, lue dans la table
d'état, et jamais depuis l'horloge : les deux dates ne coïncident pas, et une tranche entière de la
distribution bascule selon le choix.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "facturation"

# Les tranches d'ancienneté, en jours. Ce ne sont pas des seuils métier mais un découpage
# d'affichage ; elles sont écrites ici et non dérivées des données, ce qui est dit à l'écran.
TRANCHES_ANCIENNETE = (30, 60, 90, 180)

REQUETES = {
    "facturation_montants_par_type": """
        select type_episode, service_emetteur,
               count(*) as factures,
               sum(montant_total) as montant,
               sum(montant_total) / sum(sum(montant_total)) over () as part
        from fct_facturation
        {filtre}
        group by type_episode, service_emetteur
        order by type_episode, service_emetteur
    """,
    "facturation_part_organisme_patient": """
        select type_episode,
               sum(part_organisme) as part_organisme,
               sum(part_patient) as part_patient,
               sum(part_organisme) / nullif(sum(montant_total), 0) as taux_organisme
        from fct_facturation
        {filtre}
        group by type_episode
        order by type_episode
    """,
    "facturation_ecart_total_lignes": """
        select count(*) filter (where montant_total is distinct from montant_lignes)
                   as factures_en_ecart,
               count(*) as factures_examinees,
               coalesce(sum(abs(montant_total - montant_lignes))
                   filter (where montant_total is distinct from montant_lignes), 0) as cumul,
               coalesce(max(abs(montant_total - montant_lignes)), 0) as divergence_maximale
        from fct_facturation
        {filtre}
    """,
    # Lit l'agrégat de recouvrement : il n'existe aucune table de faits des créances, ce que la
    # mention de source affiche.
    "facturation_taux_recouvrement": """
        select sum(montant_du) as creances_nees,
               sum(montant_recouvre) as creances_recouvrees,
               sum(montant_recouvre) / nullif(sum(montant_du), 0) as taux
        from agg_recouvrement
        {filtre}
    """,
    # Deux restrictions et non une : le dénominateur se date par la facture, le numérateur par
    # l'encaissement. C'est exactement la réserve que le registre déclare pour cet indicateur, et
    # c'est pourquoi la clause générique ne peut pas s'appliquer ici — elle ne sait porter qu'une
    # seule colonne de date, alors que les deux membres du rapport n'ont pas la même.
    "facturation_taux_encaissement": """
        select (select sum(montant_total) from fct_facturation {filtre_facture})
                   as montant_facture,
               (select sum(montant) from fct_encaissement {filtre_encaissement})
                   as montant_encaisse,
               (select sum(montant) from fct_encaissement {filtre_encaissement})
                   / nullif(
                       (select sum(montant_total) from fct_facturation {filtre_facture}), 0
                     ) as taux
    """,
    # L'ancienneté se compte depuis la date de référence des données, lue dans la table d'état.
    "facturation_anciennete_creances": """
        with reference as (select max(date_reference_donnees) as jour from instantane_etat),
        -- Une créance porte une ligne par date d'extraction : sommer toutes les lignes
        -- surcompterait les créances vues plusieurs fois. Seul le dernier instantané de chaque
        -- créance est retenu, comme le fait l'agrégat de recouvrement.
        dernier_instantane as (
            select distinct on (n_creance)
                   n_creance, montant_restant, date_naissance_creance
            from int_creances
            order by n_creance, date_extraction desc
        ),
        creances as (
            select c.montant_restant,
                   (select jour from reference) - c.date_naissance_creance as anciennete
            from dernier_instantane c
            where c.montant_restant > 0
        )
        select case
                   when anciennete <= %(borne_a)s then '1 — jusqu''à %(borne_a)s jours'
                   when anciennete <= %(borne_b)s then '2 — de %(borne_a)s à %(borne_b)s jours'
                   when anciennete <= %(borne_c)s then '3 — de %(borne_b)s à %(borne_c)s jours'
                   when anciennete <= %(borne_d)s then '4 — de %(borne_c)s à %(borne_d)s jours'
                   else '5 — plus de %(borne_d)s jours'
               end as tranche,
               count(*) as creances,
               sum(montant_restant) as montant_restant,
               min(anciennete) as anciennete_minimale,
               max(anciennete) as anciennete_maximale
        from creances
        group by 1
        order by 1
    """,
    "facturation_aboutissement_relances": """
        select sum(n_relances) as relances_emises,
               sum(n_relances_abouties) as relances_abouties,
               sum(n_relances_abouties)::numeric / nullif(sum(n_relances), 0) as taux
        from agg_recouvrement
        {filtre}
    """,
    # La famille d'épisode se lit sur la table des passages, qui réunit les trois types. La table
    # des séjours, elle, ne porte aucune clé de facturation : le rattachement passe par le passage,
    # ce qui a été vérifié plutôt que supposé.
    "facturation_episodes_non_factures": """
        select p.type_passage as famille,
               date_trunc('month', p.date_entree)::date as mois,
               count(*) as episodes,
               count(*) filter (where f.n_facture is null) as non_factures,
               count(*) filter (where f.n_facture is null)::numeric / count(*) as part
        from fct_passage p
        left join fct_facturation f on f.n_episode = p.n_passage
        {filtre}
        group by p.type_passage, date_trunc('month', p.date_entree)
        order by famille, mois
    """,
}

FAMILLES_LISIBLES = {
    "C": "Consultations",
    "H": "Hospitalisations",
    "U": "Urgences",
}


def _montant(valeur) -> str:
    return f"{float(valeur):,.2f}".replace(",", " ").replace(".", ",")


def _pourcentage(valeur) -> str:
    return f"{100 * float(valeur):.2f} %".replace(".", ",")


def rendre() -> None:
    rendu.en_tete("Facturation")
    bornes = lecture.interroger(
        "select min(date_facture) as debut, max(date_facture) as fin from fct_facturation"
    )
    periode = rendu.filtre_de_page(PAGE, (bornes["debut"][0], bornes["fin"][0]))

    def _clause(colonne: str) -> str:
        """La restriction sur une colonne nommée ici, la période venant du filtre de la page.

        `rendu.clause_periode` ne convient pas au taux d'encaissement : elle lit la colonne de date
        déclarée au registre, et cette entrée-là en déclare deux — une par membre du rapport. La
        période reste celle du filtre de page, jamais une constante.
        """
        if periode is None:
            return ""
        debut, fin = periode
        return f"where {colonne} between date '{debut:%Y-%m-%d}' and date '{fin:%Y-%m-%d}'"

    def q(identifiant: str, **parametres):
        requete = REQUETES[identifiant]
        if "{filtre}" in requete:
            requete = requete.format(filtre=rendu.clause_periode(identifiant, periode))
        if "{filtre_facture}" in requete:
            requete = requete.format(
                filtre_facture=_clause("date_facture"),
                filtre_encaissement=_clause("jour_encaissement"),
            )
        return lecture.interroger(requete % parametres if parametres else requete)

    rendu.titre_indicateur("facturation_montants_par_type")
    montants = q("facturation_montants_par_type")
    st.bar_chart(
        rendu.en_nombres(montants, "montant", "part"),
        x="service_emetteur",
        y="montant",
        color="type_episode",
        x_label="Service émetteur",
        y_label="Montant facturé",
    )
    st.dataframe(montants, hide_index=True)

    rendu.titre_indicateur("facturation_part_organisme_patient")
    parts = q("facturation_part_organisme_patient")
    st.bar_chart(
        rendu.en_nombres(parts, "part_organisme", "part_patient"),
        x="type_episode",
        y=["part_organisme", "part_patient"],
        x_label="Type d'épisode",
        y_label="Montant",
    )
    st.dataframe(parts, hide_index=True)

    # Les deux taux, côte à côte. Ils ne se lisent pas l'un sans l'autre.
    st.divider()
    st.markdown("### Recouvrement et encaissement")
    st.caption(
        "Ces deux taux répondent à deux questions différentes et se lisent ensemble. "
        "Le **taux de recouvrement** rapporte les créances recouvrées aux créances nées : il ne "
        "porte que sur ce qui est devenu créance. Le **taux d'encaissement** rapporte le montant "
        "encaissé au montant facturé : il porte sur toute la facturation. Les dénominateurs n'ont "
        "ni la même taille ni le même sens, et l'écart entre les deux taux ne mesure donc aucune "
        "dégradation."
    )
    gauche, droite = st.columns(2)
    with gauche:
        rendu.titre_indicateur("facturation_taux_recouvrement")
        recouvrement = q("facturation_taux_recouvrement")
        ligne = recouvrement.iloc[0]
        st.metric("Taux de recouvrement", _pourcentage(ligne["taux"]))
        st.caption(
            f"{_montant(ligne['creances_recouvrees'])} recouvrés sur "
            f"{_montant(ligne['creances_nees'])} de créances nées."
        )
    with droite:
        rendu.titre_indicateur("facturation_taux_encaissement")
        encaissement = q("facturation_taux_encaissement")
        ligne = encaissement.iloc[0]
        st.metric("Taux d'encaissement", _pourcentage(ligne["taux"]))
        st.caption(
            f"{_montant(ligne['montant_encaisse'])} encaissés sur "
            f"{_montant(ligne['montant_facture'])} facturés, sur la période retenue."
        )
    st.divider()

    rendu.titre_indicateur("facturation_anciennete_creances")
    anciennete = q(
        "facturation_anciennete_creances",
        borne_a=TRANCHES_ANCIENNETE[0],
        borne_b=TRANCHES_ANCIENNETE[1],
        borne_c=TRANCHES_ANCIENNETE[2],
        borne_d=TRANCHES_ANCIENNETE[3],
    )
    st.caption(
        "L'ancienneté est comptée depuis la date de référence des données affichée en tête de "
        "page, et non depuis la date du jour : ces deux dates ne coïncident pas, et le découpage "
        "en tranches basculerait d'un cran si l'on comptait depuis l'horloge. Les bornes des "
        "tranches sont un découpage d'affichage, non des seuils de gestion."
    )
    st.bar_chart(
        rendu.en_nombres(anciennete, "montant_restant"),
        x="tranche",
        y="montant_restant",
        x_label="Tranche d'ancienneté",
        y_label="Montant restant dû",
    )
    st.dataframe(anciennete, hide_index=True)

    rendu.titre_indicateur("facturation_aboutissement_relances")
    relances = q("facturation_aboutissement_relances").iloc[0]
    colonnes = st.columns(3)
    with colonnes[0]:
        st.metric("Relances émises", f"{int(relances['relances_emises'])}")
    with colonnes[1]:
        st.metric("Relances abouties", f"{int(relances['relances_abouties'])}")
    with colonnes[2]:
        st.metric("Taux d'aboutissement", _pourcentage(relances["taux"]))

    rendu.titre_indicateur("facturation_ecart_total_lignes")
    ecart = q("facturation_ecart_total_lignes").iloc[0]
    colonnes = st.columns(3)
    with colonnes[0]:
        st.metric(
            "Factures en écart",
            f"{int(ecart['factures_en_ecart'])} sur {int(ecart['factures_examinees'])}",
        )
    with colonnes[1]:
        st.metric("Montant cumulé de l'écart", _montant(ecart["cumul"]))
    with colonnes[2]:
        st.metric("Divergence maximale", _montant(ecart["divergence_maximale"]))

    rendu.titre_indicateur("facturation_episodes_non_factures")
    non_factures = q("facturation_episodes_non_factures")
    non_factures = non_factures.assign(
        famille=non_factures["famille"].map(lambda code: FAMILLES_LISIBLES.get(code, code))
    )
    st.caption(
        "Les familles sont lues sur la table des passages, qui les réunit toutes. La table des "
        "séjours ne porte aucune clé de facturation : le rattachement d'une hospitalisation à sa "
        "facture passe par le passage correspondant, ce qui a été vérifié et non supposé."
    )
    st.line_chart(
        rendu.en_nombres(non_factures, "part"),
        x="mois",
        y="part",
        color="famille",
        x_label="Mois",
        y_label="Part des épisodes non facturés",
    )
    st.dataframe(non_factures, hide_index=True)


rendre()
