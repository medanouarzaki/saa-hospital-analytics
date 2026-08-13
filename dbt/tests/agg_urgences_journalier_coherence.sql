{#
    Cohérence de agg_urgences_journalier. Quatre propriétés, chacune l'égalité de
    deux quantités calculées indépendamment, aucun littéral.
#}

with grain_duplique as (
    select
        jour,
        niveau_tri,
        count(*) as n
    from {{ ref('agg_urgences_journalier') }}
    group by jour, niveau_tri
    having count(*) > 1
),

somme_passages as (
    select sum(nb_passages) as n from {{ ref('agg_urgences_journalier') }}
),

decompte_passages as (
    select count(*) as n from {{ ref('fct_passage_urgence') }}
),

lignes_decomposition_orientation_fausse as (
    select count(*) as n
    from {{ ref('agg_urgences_journalier') }}
    where n_retour_domicile + n_hospitalisation + n_transfert + n_autre_orientation != nb_passages
),

niveaux_tri_agregat as (
    select count(distinct niveau_tri) as n from {{ ref('agg_urgences_journalier') }}
),

niveaux_tri_fait as (
    select count(distinct niveau_tri) as n from {{ ref('fct_passage_urgence') }}
)

select
    somme_passages.n as somme_passages,
    decompte_passages.n as decompte_passages,
    lignes_decomposition_orientation_fausse.n as lignes_decomposition_orientation_fausse,
    niveaux_tri_agregat.n as niveaux_tri_agregat,
    niveaux_tri_fait.n as niveaux_tri_fait,
    (select count(*) from grain_duplique) as grain_duplique
from somme_passages
cross join decompte_passages
cross join lignes_decomposition_orientation_fausse
cross join niveaux_tri_agregat
cross join niveaux_tri_fait
where
    exists (select 1 from grain_duplique)
    or somme_passages.n != decompte_passages.n
    or lignes_decomposition_orientation_fausse.n > 0
    or niveaux_tri_agregat.n != niveaux_tri_fait.n
