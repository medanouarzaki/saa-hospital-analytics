{#
    Complétude bidirectionnelle de dim_organisme : l'ensemble des code_organisme de la dimension égale
    l'union recalculée indépendamment depuis les colonnes intermediate de la famille organisme —
    l'union est réécrite ici, pas déléguée à dim_organisme.sql, pour que ce test garde le modèle
    contre toute dérive future (filtre ajouté, colonne oubliée) sans être vrai par construction.
#}

with dans_la_dimension as (
    select code_organisme
    from {{ ref('dim_organisme') }}
),

recalcule_independamment as (

    select distinct compagnie_assurance as code_organisme
    from {{ ref('int_patients') }}
    where nullif(compagnie_assurance, '') is not null

    union

    select distinct organisme as code_organisme
    from {{ ref('int_prises_en_charge') }}
    where nullif(organisme, '') is not null

),

manquants_a_la_dimension as (
    select code_organisme from recalcule_independamment
    except
    select code_organisme from dans_la_dimension
),

manquants_au_recalcul as (
    select code_organisme from dans_la_dimension
    except
    select code_organisme from recalcule_independamment
)

select
    code_organisme,
    'absent_de_la_dimension' as anomalie
from manquants_a_la_dimension
union all
select
    code_organisme,
    'absent_du_recalcul' as anomalie
from manquants_au_recalcul
