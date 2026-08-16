"""Page d'activité : les six indicateurs que le registre déclare pour elle.

Chaque requête recalcule depuis les tables de faits de l'instantané, et ne reprend jamais une
colonne déjà agrégée. Chaque valeur affichée a été confrontée à une seconde mesure écrite
autrement, et chaque requête a été chronométrée avant d'être retenue : la forme jointe ou groupée
est employée partout, la sous-requête corrélée ayant été mesurée coûteuse d'un à trois ordres de
grandeur sur ce jeu de données.

Les trois familles d'événements sont réunies par une union plutôt que par trois requêtes séparées :
une seule lecture, un seul passage sur chaque table, et une forme unique à confronter.

Les codes de dimension s'affichent tels quels : quatre des six dimensions ne portent que leur clé
naturelle, sans attribut, et aucun libellé n'est inventé ici.
"""

from __future__ import annotations

import streamlit as st

from dashboard import lecture, rendu

PAGE = "activite"

# Les trois familles d'événements, avec leur table et leur colonne de date. Cette correspondance
# est la seule chose écrite en dur : elle relie un fait à sa date, ce que le registre déclare sans
# dire quelle colonne appartient à quelle table.
FAMILLES = (
    ("Consultations", "fct_rendez_vous", "date_rendez_vous"),
    ("Passages", "fct_passage", "date_entree"),
    ("Admissions", "fct_sejour", "jour_admission"),
)

_UNION_JOURS = " union all ".join(
    f"select {colonne} as jour, n_ipp, '{nom}' as famille from {table}"
    for nom, table, colonne in FAMILLES
)

REQUETES = {
    "activite_volume_journalier": f"""
        select jour, famille, count(*) as evenements
        from ({_UNION_JOURS}) as evenements
        where jour is not null
        group by jour, famille
        order by jour, famille
    """,
    "activite_patients_distincts": f"""
        select jour, famille, count(*) as evenements,
               count(distinct n_ipp) as patients
        from ({_UNION_JOURS}) as evenements
        where jour is not null
        group by jour, famille
        order by jour, famille
    """,
    # Le volume moyen par jour de semaine se calcule sur les jours du CALENDRIER, non sur les jours
    # où un événement a eu lieu : diviser par le nombre de jours observés surestimerait les jours
    # creux en les excluant du dénominateur.
    "activite_profil_semaine": f"""
        with evenements as (
            select jour, famille from ({_UNION_JOURS}) as tous where jour is not null
        ),
        bornes as (select min(jour) as debut, max(jour) as fin from evenements),
        calendrier as (
            select d.date_jour, d.jour_semaine_iso
            from dim_date d, bornes b
            where d.date_jour between b.debut and b.fin
        ),
        jours as (
            select jour_semaine_iso, count(*) as nb_jours from calendrier group by jour_semaine_iso
        ),
        comptes as (
            select c.jour_semaine_iso, e.famille, count(*) as evenements
            from calendrier c join evenements e on e.jour = c.date_jour
            group by c.jour_semaine_iso, e.famille
        )
        select j.jour_semaine_iso, f.famille,
               coalesce(t.evenements, 0)::numeric / j.nb_jours as moyenne_journaliere
        from jours j
        cross join (select distinct famille from evenements) f
        left join comptes t
               on t.jour_semaine_iso = j.jour_semaine_iso and t.famille = f.famille
        order by j.jour_semaine_iso, f.famille
    """,
    "activite_effet_ramadan": f"""
        with evenements as (
            select jour from ({_UNION_JOURS}) as tous where jour is not null
        ),
        bornes as (select min(jour) as debut, max(jour) as fin from evenements),
        calendrier as (
            select d.date_jour, d.est_ramadan
            from dim_date d, bornes b
            where d.date_jour between b.debut and b.fin
        )
        select case when c.est_ramadan then 'Ramadan' else 'Hors Ramadan' end as periode,
               count(distinct c.date_jour) as jours,
               count(e.jour) as evenements,
               count(e.jour)::numeric / count(distinct c.date_jour) as moyenne_journaliere
        from calendrier c
        left join evenements e on e.jour = c.date_jour
        group by c.est_ramadan
        order by periode
    """,
    "activite_effet_calendaire": f"""
        with evenements as (
            select jour from ({_UNION_JOURS}) as tous where jour is not null
        ),
        bornes as (select min(jour) as debut, max(jour) as fin from evenements),
        calendrier as (
            select d.date_jour,
                   case when d.est_ferie then 'Jours fériés'
                        when d.est_weekend then 'Week-ends'
                        else 'Jours ouvrés' end as nature
            from dim_date d, bornes b
            where d.date_jour between b.debut and b.fin
        )
        select c.nature,
               count(distinct c.date_jour) as jours,
               count(e.jour) as evenements,
               count(e.jour)::numeric / count(distinct c.date_jour) as moyenne_journaliere
        from calendrier c
        left join evenements e on e.jour = c.date_jour
        group by c.nature
        order by c.nature
    """,
    # L'heure est extraite sous un fuseau fixé par le module de lecture : sans cela, la répartition
    # horaire dépendrait du fuseau de la session qui l'interroge.
    "activite_profil_horaire": """
        select heure, famille, count(*) as evenements
        from (
            select extract(hour from date_heure_entree)::int as heure,
                   'Consultations' as famille from fct_passage
            union all
            select extract(hour from date_heure_arrivee)::int,
                   'Urgences' from fct_passage_urgence
            union all
            select extract(hour from date_heure_admission)::int,
                   'Admissions' from fct_sejour
        ) as arrivees
        where heure is not null
        group by heure, famille
        order by heure, famille
    """,
}


def _filtre_periode(volumes) -> tuple:
    """Le filtre de période est porté par la page, et n'apparaît que parce que le registre déclare
    ses six indicateurs filtrables. Ses bornes viennent des données, non d'une constante."""
    debut, fin = volumes["jour"].min(), volumes["jour"].max()
    choix = st.date_input(
        "Période observée",
        value=(debut, fin),
        min_value=debut,
        max_value=fin,
    )
    if isinstance(choix, tuple) and len(choix) == 2:
        return choix
    return debut, fin


def rendre() -> None:
    rendu.en_tete("Activité")

    volumes = lecture.interroger(REQUETES["activite_volume_journalier"])
    debut, fin = _filtre_periode(volumes)

    rendu.titre_indicateur("activite_volume_journalier")
    retenu = volumes[(volumes["jour"] >= debut) & (volumes["jour"] <= fin)]
    st.line_chart(retenu, x="jour", y="evenements", color="famille")

    rendu.titre_indicateur("activite_patients_distincts")
    patients = lecture.interroger(REQUETES["activite_patients_distincts"])
    patients = patients[(patients["jour"] >= debut) & (patients["jour"] <= fin)]
    colonnes = st.columns(len(FAMILLES))
    for colonne, (nom, _, _) in zip(colonnes, FAMILLES, strict=True):
        part = patients[patients["famille"] == nom]
        with colonne:
            st.metric(
                nom,
                f"{int(part['patients'].sum()):,}".replace(",", " "),
                help="Patients distincts par jour, cumulés sur la période retenue",
            )
    st.line_chart(patients, x="jour", y="patients", color="famille")

    rendu.titre_indicateur("activite_profil_semaine")
    st.bar_chart(
        lecture.interroger(REQUETES["activite_profil_semaine"]),
        x="jour_semaine_iso",
        y="moyenne_journaliere",
        color="famille",
        x_label="Jour de la semaine (1 = lundi)",
        y_label="Événements par jour",
    )

    gauche, droite = st.columns(2)
    with gauche:
        rendu.titre_indicateur("activite_effet_ramadan")
        st.dataframe(lecture.interroger(REQUETES["activite_effet_ramadan"]), hide_index=True)
    with droite:
        rendu.titre_indicateur("activite_effet_calendaire")
        st.dataframe(lecture.interroger(REQUETES["activite_effet_calendaire"]), hide_index=True)

    rendu.titre_indicateur("activite_profil_horaire")
    st.bar_chart(
        lecture.interroger(REQUETES["activite_profil_horaire"]),
        x="heure",
        y="evenements",
        color="famille",
        x_label="Heure de la journée",
        y_label="Événements",
    )


rendre()
