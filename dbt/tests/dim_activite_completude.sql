{#
    Complétude bidirectionnelle de dim_activite : l'ensemble des code_activite de la dimension égale
    l'union recalculée indépendamment depuis les colonnes intermediate de la famille activite —
    l'union est réécrite ici, pas déléguée à dim_activite.sql, pour que ce test garde le modèle
    contre toute dérive future (filtre ajouté, colonne oubliée) sans être vrai par construction.
#}

with dans_la_dimension as (
    select code_activite
    from {{ ref('dim_activite') }}
),

recalcule_independamment as (

    select distinct activite as code_activite
    from {{ ref('int_passages') }}
    where nullif(activite, '') is not null

    union

    select distinct activite as code_activite
    from {{ ref('int_rendez_vous') }}
    where nullif(activite, '') is not null

    union

    select distinct liste_attente_activite as code_activite
    from {{ ref('int_rendez_vous') }}
    where nullif(liste_attente_activite, '') is not null

),

manquants_a_la_dimension as (
    select code_activite from recalcule_independamment
    except
    select code_activite from dans_la_dimension
),

manquants_au_recalcul as (
    select code_activite from dans_la_dimension
    except
    select code_activite from recalcule_independamment
)

select
    code_activite,
    'absent_de_la_dimension' as anomalie
from manquants_a_la_dimension
union all
select
    code_activite,
    'absent_du_recalcul' as anomalie
from manquants_au_recalcul
