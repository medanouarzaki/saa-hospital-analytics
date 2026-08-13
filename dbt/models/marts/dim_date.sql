{#
    Dimension calendrier, sur l'étendue portée par les variables dim_date_debut/dim_date_fin
    (dbt/dbt_project.yml) — aucune date en dur. Les colonnes est_ferie/est_ramadan et leurs
    libellés viennent du seed calendrier_marocain, lui-même dérivé mécaniquement de
    generator/config/calendrier.yml (voir docs/calendrier/generer_seed_calendrier.py).
#}

with jours as (
    select generate_series(
        '{{ var("dim_date_debut") }}'::date,
        '{{ var("dim_date_fin") }}'::date,
        interval '1 day'
    )::date as date_jour
),

feries as (
    select
        jour,
        string_agg(libelle, ',' order by libelle) as libelles_feries
    from {{ ref('calendrier_marocain') }}
    where categorie in ('ferie_fixe', 'ferie_mobile')
    group by jour
),

observances_ramadan as (
    select jour
    from {{ ref('calendrier_marocain') }}
    where categorie = 'ramadan'
)

select
    jours.date_jour,
    feries.libelles_feries as libelle_ferie,
    extract(year from jours.date_jour)::int as annee,
    extract(quarter from jours.date_jour)::int as trimestre,
    extract(month from jours.date_jour)::int as mois,
    extract(day from jours.date_jour)::int as jour,
    extract(isodow from jours.date_jour)::int as jour_semaine_iso,
    extract(isodow from jours.date_jour)::int in (6, 7) as est_weekend,
    feries.jour is not null as est_ferie,
    observances_ramadan.jour is not null as est_ramadan
from jours
left join feries on jours.date_jour = feries.jour
left join observances_ramadan on jours.date_jour = observances_ramadan.jour
