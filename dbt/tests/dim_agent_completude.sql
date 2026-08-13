{#
    Complétude bidirectionnelle de dim_agent : l'ensemble des code_agent de la dimension égale
    l'union recalculée indépendamment depuis les colonnes intermediate de la famille agent —
    l'union est réécrite ici, pas déléguée à dim_agent.sql, pour que ce test garde le modèle
    contre toute dérive future (filtre ajouté, colonne oubliée) sans être vrai par construction.
#}

with dans_la_dimension as (
    select code_agent
    from {{ ref('dim_agent') }}
),

recalcule_independamment as (

    select distinct cree_par as code_agent
    from {{ ref('int_patients') }}
    where nullif(cree_par, '') is not null

    union

    select distinct modifie_par as code_agent
    from {{ ref('int_patients') }}
    where nullif(modifie_par, '') is not null

    union

    select distinct cree_par as code_agent
    from {{ ref('int_rendez_vous') }}
    where nullif(cree_par, '') is not null

    union

    select distinct modifie_par as code_agent
    from {{ ref('int_rendez_vous') }}
    where nullif(modifie_par, '') is not null

    union

    select distinct confirme_par as code_agent
    from {{ ref('int_rendez_vous') }}
    where nullif(confirme_par, '') is not null

    union

    select distinct annule_par as code_agent
    from {{ ref('int_rendez_vous') }}
    where nullif(annule_par, '') is not null

    union

    select distinct cree_par as code_agent
    from {{ ref('int_passages') }}
    where nullif(cree_par, '') is not null

    union

    select distinct cree_par as code_agent
    from {{ ref('int_factures') }}
    where nullif(cree_par, '') is not null

    union

    select distinct regisseur as code_agent
    from {{ ref('int_encaissements') }}
    where nullif(regisseur, '') is not null

),

manquants_a_la_dimension as (
    select code_agent from recalcule_independamment
    except
    select code_agent from dans_la_dimension
),

manquants_au_recalcul as (
    select code_agent from dans_la_dimension
    except
    select code_agent from recalcule_independamment
)

select
    code_agent,
    'absent_de_la_dimension' as anomalie
from manquants_a_la_dimension
union all
select
    code_agent,
    'absent_du_recalcul' as anomalie
from manquants_au_recalcul
