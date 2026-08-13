{#
    Continuité sans trou : le décompte de dim_date égale le nombre de jours entre les deux
    variables du projet, calculé par arithmétique de dates SQL — aucun littéral, deux mesures
    indépendantes (un count(*), une soustraction de dates).
#}

with decompte_modele as (
    select count(*) as n from {{ ref('dim_date') }}
),

decompte_attendu as (
    select
        (
            '{{ var("dim_date_fin") }}'::date - '{{ var("dim_date_debut") }}'::date + 1
        ) as n
)

select
    decompte_modele.n as decompte_modele,
    decompte_attendu.n as decompte_attendu
from decompte_modele
cross join decompte_attendu
where decompte_modele.n != decompte_attendu.n
