{#
    dim_organisme : clé naturelle code_organisme, aucun libellé inventé — union des colonnes de la
    famille organisme mesurée depuis le registre, vides exclus. Pas de
    clé de substitution : la vue reste déterministe d'une exécution à l'autre.
#}

with codes as (

    select distinct compagnie_assurance as code_organisme
    from {{ ref('int_patients') }}
    where nullif(compagnie_assurance, '') is not null

    union

    select distinct organisme as code_organisme
    from {{ ref('int_prises_en_charge') }}
    where nullif(organisme, '') is not null

)

select distinct code_organisme from codes
