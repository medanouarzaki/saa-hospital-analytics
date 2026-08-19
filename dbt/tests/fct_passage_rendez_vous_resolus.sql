{#
    Propriété reportée depuis les faits de flux : le nombre de passages dont
    le rendez-vous est résolu égale le nombre de rendez-vous honorés. Deux quantités
    calculées indépendamment, l'une sur fct_passage, l'autre sur fct_rendez_vous,
    aucun littéral. Mesuré vrai avant écriture.
#}

with passages_rdv_resolu as (
    select count(*) as n
    from {{ ref('fct_passage') }}
    where n_rdv_resolu is not null
),

rendez_vous_honores as (
    select count(*) as n
    from {{ ref('fct_rendez_vous') }}
    where est_honore
)

select
    passages_rdv_resolu.n as passages_rdv_resolu,
    rendez_vous_honores.n as rendez_vous_honores
from passages_rdv_resolu
cross join rendez_vous_honores
where passages_rdv_resolu.n != rendez_vous_honores.n
