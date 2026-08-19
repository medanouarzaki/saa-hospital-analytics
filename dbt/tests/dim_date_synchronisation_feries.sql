{#
    Synchronisation des fériés : égalité d'ensembles bidirectionnelle entre les jours est_ferie
    de dim_date et les jours de catégorie ferie_fixe/ferie_mobile du seed — except dans les deux
    sens, union all des deux anomalies possibles.

    Le seed explose les fériés fixes sur des ANNÉES complètes (2023 à 2026) alors que dim_date ne
    couvre qu'à partir du 1er août 2023 (var dim_date_debut) : cinq fériés fixes de 2023
    (janvier, mai, juillet) tombent avant cette borne et sont hors de portée de dim_date sans que
    ce soit une divergence. Comparaison restreinte à l'étendue réelle de dim_date, par les mêmes
    variables — mesuré, pas supposé.
#}

with jours_dim as (
    select date_jour
    from {{ ref('dim_date') }}
    where est_ferie
),

jours_seed as (
    select distinct jour
    from {{ ref('calendrier_marocain') }}
    where
        categorie in ('ferie_fixe', 'ferie_mobile')
        and jour >= '{{ var("dim_date_debut") }}'::date
        and jour <= '{{ var("dim_date_fin") }}'::date
),

manquants_au_seed as (
    select date_jour as jour from jours_dim
    except
    select jour from jours_seed
),

manquants_a_dim_date as (
    select jour from jours_seed
    except
    select date_jour from jours_dim
)

select
    jour,
    'ferie_dans_dim_date_absent_du_seed' as anomalie
from manquants_au_seed

union all

select
    jour,
    'ferie_dans_le_seed_absent_de_dim_date' as anomalie
from manquants_a_dim_date
