{#
    Cohérence de agg_activite_journaliere. Trois propriétés, chacune l'égalité (ou
    l'inégalité bornante) de deux quantités calculées indépendamment, aucun littéral.
#}

with grain_duplique as (
    select
        jour,
        type_evenement,
        service,
        activite,
        count(*) as n
    from {{ ref('agg_activite_journaliere') }}
    group by jour, type_evenement, service, activite
    having count(*) > 1
),

somme_rendez_vous as (
    select sum(nb_evenements) as n
    from {{ ref('agg_activite_journaliere') }}
    where type_evenement = 'RENDEZ_VOUS'
),

decompte_rendez_vous as (
    select count(*) as n from {{ ref('fct_rendez_vous') }}
),

somme_passage_c as (
    select sum(nb_evenements) as n
    from {{ ref('agg_activite_journaliere') }}
    where type_evenement = 'PASSAGE_C'
),

decompte_passage_c as (
    select count(*) as n from {{ ref('fct_passage') }}
    where type_passage = 'C'
),

somme_passage_h as (
    select sum(nb_evenements) as n
    from {{ ref('agg_activite_journaliere') }}
    where type_evenement = 'PASSAGE_H'
),

decompte_passage_h as (
    select count(*) as n from {{ ref('fct_passage') }}
    where type_passage = 'H'
),

somme_passage_u as (
    select sum(nb_evenements) as n
    from {{ ref('agg_activite_journaliere') }}
    where type_evenement = 'PASSAGE_U'
),

decompte_passage_u as (
    select count(*) as n from {{ ref('fct_passage') }}
    where type_passage = 'U'
),

somme_admission as (
    select sum(nb_evenements) as n
    from {{ ref('agg_activite_journaliere') }}
    where type_evenement = 'ADMISSION_SEJOUR'
),

decompte_admission as (
    select count(*) as n from {{ ref('fct_sejour') }}
),

somme_sortie as (
    select sum(nb_evenements) as n
    from {{ ref('agg_activite_journaliere') }}
    where type_evenement = 'SORTIE_SEJOUR'
),

decompte_sortie as (
    select count(*) as n from {{ ref('fct_sejour') }}
    where est_clos
),

lignes_borne_violee as (
    select count(*) as n
    from {{ ref('agg_activite_journaliere') }}
    where nb_patients_distincts > nb_evenements
)

select
    somme_rendez_vous.n as somme_rendez_vous,
    decompte_rendez_vous.n as decompte_rendez_vous,
    somme_passage_c.n as somme_passage_c,
    decompte_passage_c.n as decompte_passage_c,
    somme_passage_h.n as somme_passage_h,
    decompte_passage_h.n as decompte_passage_h,
    somme_passage_u.n as somme_passage_u,
    decompte_passage_u.n as decompte_passage_u,
    somme_admission.n as somme_admission,
    decompte_admission.n as decompte_admission,
    somme_sortie.n as somme_sortie,
    decompte_sortie.n as decompte_sortie,
    lignes_borne_violee.n as lignes_borne_violee,
    (select count(*) from grain_duplique) as grain_duplique
from somme_rendez_vous
cross join decompte_rendez_vous
cross join somme_passage_c
cross join decompte_passage_c
cross join somme_passage_h
cross join decompte_passage_h
cross join somme_passage_u
cross join decompte_passage_u
cross join somme_admission
cross join decompte_admission
cross join somme_sortie
cross join decompte_sortie
cross join lignes_borne_violee
where
    exists (select 1 from grain_duplique)
    or somme_rendez_vous.n != decompte_rendez_vous.n
    or somme_passage_c.n != decompte_passage_c.n
    or somme_passage_h.n != decompte_passage_h.n
    or somme_passage_u.n != decompte_passage_u.n
    or somme_admission.n != decompte_admission.n
    or somme_sortie.n != decompte_sortie.n
    or lignes_borne_violee.n > 0
