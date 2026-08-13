{#
    dim_agent : clé naturelle code_agent, aucun libellé inventé — union des colonnes de la
    famille agent mesurée depuis le registre (voir le rapport de ce lot), vides exclus. Pas de
    clé de substitution : la vue reste déterministe d'une exécution à l'autre.
#}

with codes as (

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

)

select distinct code_agent from codes
