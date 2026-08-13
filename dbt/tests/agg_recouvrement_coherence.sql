{#
    Cohérence de agg_recouvrement. Quatre propriétés, chacune l'égalité (ou l'inégalité
    bornante) de deux quantités calculées indépendamment, aucun littéral.
#}

with grain_duplique as (
    select
        jour,
        type_debiteur,
        count(*) as n
    from {{ ref('agg_recouvrement') }}
    group by jour, type_debiteur
    having count(*) > 1
),

somme_creances as (
    select sum(n_creances) as n from {{ ref('agg_recouvrement') }}
),

decompte_creances as (
    select count(distinct n_creance) as n from {{ ref('int_creances') }}
),

lignes_decomposition_montant_fausse as (
    select count(*) as n
    from {{ ref('agg_recouvrement') }}
    where montant_recouvre + montant_restant != montant_du
),

somme_relances as (
    select sum(n_relances) as n from {{ ref('agg_recouvrement') }}
),

decompte_relances as (
    select count(*) as n from {{ ref('int_relances') }}
),

lignes_borne_violee as (
    select count(*) as n
    from {{ ref('agg_recouvrement') }}
    where n_relances_abouties > n_relances
)

select
    somme_creances.n as somme_creances,
    decompte_creances.n as decompte_creances,
    lignes_decomposition_montant_fausse.n as lignes_decomposition_montant_fausse,
    somme_relances.n as somme_relances,
    decompte_relances.n as decompte_relances,
    lignes_borne_violee.n as lignes_borne_violee,
    (select count(*) from grain_duplique) as grain_duplique
from somme_creances
cross join decompte_creances
cross join lignes_decomposition_montant_fausse
cross join somme_relances
cross join decompte_relances
cross join lignes_borne_violee
where
    exists (select 1 from grain_duplique)
    or somme_creances.n != decompte_creances.n
    or lignes_decomposition_montant_fausse.n > 0
    or somme_relances.n != decompte_relances.n
    or lignes_borne_violee.n > 0
