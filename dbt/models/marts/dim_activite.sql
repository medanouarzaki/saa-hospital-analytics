{#
    dim_activite : clé naturelle code_activite, aucun libellé inventé — union des colonnes de la
    famille activite mesurée depuis le registre (voir le rapport de ce lot), vides exclus. Pas de
    clé de substitution : la vue reste déterministe d'une exécution à l'autre.
#}

with codes as (

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

)

select distinct code_activite from codes
