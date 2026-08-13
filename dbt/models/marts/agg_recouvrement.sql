{#
    Une ligne par jour de naissance de créance et type de débiteur.

    Une créance porte plusieurs instantanés (une ligne par date_extraction) : montant_du
    y est constant, montant_recouvre et montant_restant y évoluent. Sommer toutes les
    lignes surcompterait montant_du. Cet agrégat ne retient donc, par créance, QUE son
    instantané le plus récent (max date_extraction) -- toute ligne d'instantané antérieur
    est exclue.

    n_relances compte les relances émises sur les créances de la ligne (indépendant du
    nombre d'instantanés retenus, une relance n'a qu'une ligne dans source.relances).
    n_relances_abouties compte celles dont le résultat est PAYE ou PART (nomenclature
    nomenclature_resultat_relance, generator/config/nomenclatures_recouvrement.yml) --
    un aboutissement complet ou partiel, jamais SANS ni REFUS.
#}

with dernier_instantane as (
    select
        n_creance,
        date_naissance_creance,
        type_debiteur,
        montant_du,
        montant_recouvre,
        montant_restant,
        row_number() over (
            partition by n_creance order by date_extraction desc
        ) as rang
    from {{ ref('int_creances') }}
),

creances as (
    select
        n_creance,
        date_naissance_creance,
        type_debiteur,
        montant_du,
        montant_recouvre,
        montant_restant
    from dernier_instantane
    where rang = 1
),

relances as (
    select
        c.date_naissance_creance,
        c.type_debiteur,
        r.resultat
    from {{ ref('int_relances') }} as r
    inner join creances as c on r.n_creance = c.n_creance
),

relances_par_groupe as (
    select
        date_naissance_creance,
        type_debiteur,
        count(*) as n_relances,
        count(*) filter (where resultat in ('PAYE', 'PART')) as n_relances_abouties
    from relances
    group by date_naissance_creance, type_debiteur
)

select
    creances.date_naissance_creance as jour,
    creances.type_debiteur,
    count(*) as n_creances,
    sum(creances.montant_du) as montant_du,
    sum(creances.montant_recouvre) as montant_recouvre,
    sum(creances.montant_restant) as montant_restant,
    sum(creances.montant_recouvre) / sum(creances.montant_du) as taux_recouvrement,
    coalesce(relances_par_groupe.n_relances, 0) as n_relances,
    coalesce(relances_par_groupe.n_relances_abouties, 0) as n_relances_abouties
from creances
left join relances_par_groupe
    on
        creances.date_naissance_creance = relances_par_groupe.date_naissance_creance
        and creances.type_debiteur = relances_par_groupe.type_debiteur
group by
    creances.date_naissance_creance,
    creances.type_debiteur,
    relances_par_groupe.n_relances,
    relances_par_groupe.n_relances_abouties
