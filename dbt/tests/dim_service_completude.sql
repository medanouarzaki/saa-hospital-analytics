{#
    Complétude bidirectionnelle de dim_service : l'ensemble des code_service de la dimension égale
    l'union recalculée indépendamment depuis les colonnes intermediate de la famille service —
    l'union est réécrite ici, pas déléguée à dim_service.sql, pour que ce test garde le modèle
    contre toute dérive future (filtre ajouté, colonne oubliée) sans être vrai par construction.
#}

with dans_la_dimension as (
    select code_service
    from {{ ref('dim_service') }}
),

recalcule_independamment as (

    select distinct service_accueil as code_service
    from {{ ref('int_mouvements') }}
    where nullif(service_accueil, '') is not null

    union

    select distinct service_origine as code_service
    from {{ ref('int_mouvements') }}
    where nullif(service_origine, '') is not null

    union

    select distinct service_destination as code_service
    from {{ ref('int_mouvements') }}
    where nullif(service_destination, '') is not null

    union

    select distinct service as code_service
    from {{ ref('int_passages') }}
    where nullif(service, '') is not null

    union

    select distinct service_orientation as code_service
    from {{ ref('int_passages_urgences') }}
    where nullif(service_orientation, '') is not null

    union

    select distinct service_emetteur as code_service
    from {{ ref('int_factures') }}
    where nullif(service_emetteur, '') is not null

    union

    select distinct service_executant as code_service
    from {{ ref('int_lignes_facture') }}
    where nullif(service_executant, '') is not null

    union

    select distinct liste_attente_service as code_service
    from {{ ref('int_rendez_vous') }}
    where nullif(liste_attente_service, '') is not null

),

manquants_a_la_dimension as (
    select code_service from recalcule_independamment
    except
    select code_service from dans_la_dimension
),

manquants_au_recalcul as (
    select code_service from dans_la_dimension
    except
    select code_service from recalcule_independamment
)

select
    code_service,
    'absent_de_la_dimension' as anomalie
from manquants_a_la_dimension
union all
select
    code_service,
    'absent_du_recalcul' as anomalie
from manquants_au_recalcul
