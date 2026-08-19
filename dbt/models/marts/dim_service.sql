{#
    dim_service : clé naturelle code_service, aucun libellé inventé — union des colonnes de la
    famille service mesurée depuis le registre, vides exclus. Pas de
    clé de substitution : la vue reste déterministe d'une exécution à l'autre.
#}

with codes as (

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

)

select distinct code_service from codes
