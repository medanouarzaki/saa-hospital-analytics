{#
    Cohérence de agg_qualite_donnees. Cinq propriétés, chacune l'égalité (ou
    l'inégalité bornante) de deux quantités calculées indépendamment, aucun littéral.
#}

with grain_duplique as (
    select
        nom_table,
        colonne,
        count(*) as n
    from {{ ref('agg_qualite_donnees') }}
    group by nom_table, colonne
    having count(*) > 1
),

lignes_examinees_non_constantes as (
    select count(*) as n
    from (
        select
            nom_table,
            count(distinct lignes_examinees) as n_valeurs_distinctes
        from {{ ref('agg_qualite_donnees') }}
        group by nom_table
        having count(distinct lignes_examinees) > 1
    ) as t
),

lignes_quarantaine_non_constantes as (
    select count(*) as n
    from (
        select
            nom_table,
            count(distinct lignes_quarantaine) as n_valeurs_distinctes
        from {{ ref('agg_qualite_donnees') }}
        group by nom_table
        having count(distinct lignes_quarantaine) > 1
    ) as t
),

lignes_borne_violee as (
    select count(*) as n
    from {{ ref('agg_qualite_donnees') }}
    where valeurs_renseignees > lignes_examinees
),

lignes_examinees_par_table as (
    select
        nom_table,
        min(lignes_examinees) as lignes_examinees
    from {{ ref('agg_qualite_donnees') }}
    group by nom_table
),

decompte_vues as (
    select
        'int_creances' as nom_table,
        count(*) as n
    from {{ ref('int_creances') }}
    union all
    select
        'int_encaissements' as nom_table,
        count(*) as n
    from {{ ref('int_encaissements') }}
    union all
    select
        'int_factures' as nom_table,
        count(*) as n
    from {{ ref('int_factures') }}
    union all
    select
        'int_lignes_facture' as nom_table,
        count(*) as n
    from {{ ref('int_lignes_facture') }}
    union all
    select
        'int_mouvements' as nom_table,
        count(*) as n
    from {{ ref('int_mouvements') }}
    union all
    select
        'int_passages' as nom_table,
        count(*) as n
    from {{ ref('int_passages') }}
    union all
    select
        'int_passages_urgences' as nom_table,
        count(*) as n
    from {{ ref('int_passages_urgences') }}
    union all
    select
        'int_patients' as nom_table,
        count(*) as n
    from {{ ref('int_patients') }}
    union all
    select
        'int_prises_en_charge' as nom_table,
        count(*) as n
    from {{ ref('int_prises_en_charge') }}
    union all
    select
        'int_relances' as nom_table,
        count(*) as n
    from {{ ref('int_relances') }}
    union all
    select
        'int_rendez_vous' as nom_table,
        count(*) as n
    from {{ ref('int_rendez_vous') }}
),

lignes_examinees_incoherentes_avec_la_vue as (
    select count(*) as n
    from lignes_examinees_par_table as lep
    inner join decompte_vues as dv on lep.nom_table = dv.nom_table
    where lep.lignes_examinees != dv.n
),

colonnes_par_table_agregat as (
    select
        nom_table,
        count(*) as n_colonnes
    from {{ ref('agg_qualite_donnees') }}
    group by nom_table
),

colonnes_par_table_catalogue as (
    select
        table_name as nom_table,
        count(*) as n_colonnes
    from information_schema.columns
    where table_schema = 'intermediate'
    group by table_name
),

colonnes_incoherentes as (
    select count(*) as n
    from colonnes_par_table_agregat as a
    inner join colonnes_par_table_catalogue as c on a.nom_table = c.nom_table
    where a.n_colonnes != c.n_colonnes
)

select
    lignes_examinees_non_constantes.n as lignes_examinees_non_constantes,
    lignes_quarantaine_non_constantes.n as lignes_quarantaine_non_constantes,
    lignes_borne_violee.n as lignes_borne_violee,
    lignes_examinees_incoherentes_avec_la_vue.n as lignes_examinees_incoherentes_avec_la_vue,
    colonnes_incoherentes.n as colonnes_incoherentes,
    (select count(*) from grain_duplique) as grain_duplique
from lignes_examinees_non_constantes
cross join lignes_quarantaine_non_constantes
cross join lignes_borne_violee
cross join lignes_examinees_incoherentes_avec_la_vue
cross join colonnes_incoherentes
where
    exists (select 1 from grain_duplique)
    or lignes_examinees_non_constantes.n > 0
    or lignes_quarantaine_non_constantes.n > 0
    or lignes_borne_violee.n > 0
    or lignes_examinees_incoherentes_avec_la_vue.n > 0
    or colonnes_incoherentes.n > 0
