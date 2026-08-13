{#
    Cohérence des deux agrégats de rendez-vous entre eux et face au fait. Cinq
    propriétés, chacune l'égalité de deux quantités calculées indépendamment, aucun
    littéral. La dernière interdit à deux agrégats issus du même fait de raconter
    deux histoires différentes.
#}

with grain_delai as (
    select
        count(*) as lignes,
        count(distinct code_activite) as codes_distincts
    from {{ ref('agg_delai_rendez_vous') }}
),

grain_absenteisme as (
    select
        count(*) as lignes,
        count(distinct code_activite) as codes_distincts
    from {{ ref('agg_absenteisme') }}
),

decompte_fait as (
    select count(*) as n from {{ ref('fct_rendez_vous') }}
),

somme_delai as (
    select sum(n_rendez_vous) as n from {{ ref('agg_delai_rendez_vous') }}
),

somme_absenteisme as (
    select sum(n_rendez_vous) as n from {{ ref('agg_absenteisme') }}
),

total_lignes_delai as (
    select count(*) as n from {{ ref('agg_delai_rendez_vous') }}
),

lignes_delai_decomposition_juste as (
    select count(*) as n
    from {{ ref('agg_delai_rendez_vous') }}
    where n_jour_meme + n_delai_positif = n_rendez_vous
),

total_lignes_absenteisme as (
    select count(*) as n from {{ ref('agg_absenteisme') }}
),

lignes_absenteisme_decomposition_juste as (
    select count(*) as n
    from {{ ref('agg_absenteisme') }}
    where n_honores + n_absences + n_annulations + n_etat_restant = n_rendez_vous
),

codes_delai_absents_absenteisme as (
    select code_activite from {{ ref('agg_delai_rendez_vous') }}
    except
    select code_activite from {{ ref('agg_absenteisme') }}
),

codes_absenteisme_absents_delai as (
    select code_activite from {{ ref('agg_absenteisme') }}
    except
    select code_activite from {{ ref('agg_delai_rendez_vous') }}
),

codes_effectif_divergent as (
    select d.code_activite
    from {{ ref('agg_delai_rendez_vous') }} as d
    inner join {{ ref('agg_absenteisme') }} as a on d.code_activite = a.code_activite
    where d.n_rendez_vous != a.n_rendez_vous
)

select
    grain_delai.lignes as delai_lignes,
    grain_delai.codes_distincts as delai_codes_distincts,
    grain_absenteisme.lignes as absenteisme_lignes,
    grain_absenteisme.codes_distincts as absenteisme_codes_distincts,
    decompte_fait.n as fait_n,
    somme_delai.n as somme_delai,
    somme_absenteisme.n as somme_absenteisme,
    total_lignes_delai.n as total_lignes_delai,
    lignes_delai_decomposition_juste.n as lignes_delai_decomposition_juste,
    total_lignes_absenteisme.n as total_lignes_absenteisme,
    lignes_absenteisme_decomposition_juste.n as lignes_absenteisme_decomposition_juste,
    (select count(*) from codes_delai_absents_absenteisme) as codes_delai_absents_absenteisme,
    (select count(*) from codes_absenteisme_absents_delai) as codes_absenteisme_absents_delai,
    (select count(*) from codes_effectif_divergent) as codes_effectif_divergent
from grain_delai
cross join grain_absenteisme
cross join decompte_fait
cross join somme_delai
cross join somme_absenteisme
cross join total_lignes_delai
cross join lignes_delai_decomposition_juste
cross join total_lignes_absenteisme
cross join lignes_absenteisme_decomposition_juste
where
    grain_delai.lignes != grain_delai.codes_distincts
    or grain_absenteisme.lignes != grain_absenteisme.codes_distincts
    or somme_delai.n != decompte_fait.n
    or somme_absenteisme.n != decompte_fait.n
    or total_lignes_delai.n != lignes_delai_decomposition_juste.n
    or total_lignes_absenteisme.n != lignes_absenteisme_decomposition_juste.n
    or exists (select 1 from codes_delai_absents_absenteisme)
    or exists (select 1 from codes_absenteisme_absents_delai)
    or exists (select 1 from codes_effectif_divergent)
