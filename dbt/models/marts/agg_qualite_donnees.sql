{#
    Une ligne par table intermediate et par colonne (grain retenu après mesure du coût
    de conversion ligne->document sur les onze vues intermediate : ~1,78 s au total,
    loin sous le seuil de 10 s qui aurait imposé un repli sur le grain table seule --
    voir le rapport).

    Une valeur est renseignée si elle n'est ni nulle ni la chaîne vide -- vérifié par
    requête témoin sur source.patients.nom_famille_2 (0 NULL, des chaînes vides) avant
    d'être codé : la couche source ne porte jamais de NULL, seulement la chaîne vide
    pour une valeur absente.

    lignes_quarantaine et taux_quarantaine sont mesurés au niveau de la table (pas de
    la colonne, la quarantaine ne portant pas de colonne individuelle en cause) et
    répétés à l'identique sur chaque ligne de colonne de cette table -- dénormalisation
    documentée, vérifiée constante par le test de cohérence.

    Les tables quarantaine.* référencées ci-dessous ne sont déclarées dans aucune
    source dbt (le registre des champs ne régit que la couche source) : c'est l'unique
    justification de la référence directe par schéma plutôt que par ref()/source().
#}

with int_creances_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_creances') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_encaissements_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_encaissements') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_factures_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_factures') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_lignes_facture_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_lignes_facture') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_mouvements_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_mouvements') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_passages_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_passages') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_passages_urgences_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_passages_urgences') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_patients_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_patients') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_prises_en_charge_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_prises_en_charge') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_relances_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_relances') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

int_rendez_vous_kv as (
    select (kv).key as colonne, (kv).value as valeur
    from {{ ref('int_rendez_vous') }} as t, lateral jsonb_each_text(to_jsonb(t)) as kv
),

toutes_colonnes as (
    select 'int_creances' as nom_table, colonne, valeur from int_creances_kv
    union all
    select 'int_encaissements' as nom_table, colonne, valeur from int_encaissements_kv
    union all
    select 'int_factures' as nom_table, colonne, valeur from int_factures_kv
    union all
    select 'int_lignes_facture' as nom_table, colonne, valeur from int_lignes_facture_kv
    union all
    select 'int_mouvements' as nom_table, colonne, valeur from int_mouvements_kv
    union all
    select 'int_passages' as nom_table, colonne, valeur from int_passages_kv
    union all
    select 'int_passages_urgences' as nom_table, colonne, valeur from int_passages_urgences_kv
    union all
    select 'int_patients' as nom_table, colonne, valeur from int_patients_kv
    union all
    select 'int_prises_en_charge' as nom_table, colonne, valeur from int_prises_en_charge_kv
    union all
    select 'int_relances' as nom_table, colonne, valeur from int_relances_kv
    union all
    select 'int_rendez_vous' as nom_table, colonne, valeur from int_rendez_vous_kv
),

par_colonne as (
    select
        nom_table,
        colonne,
        count(*) as lignes_examinees,
        count(*) filter (where valeur is not null and valeur != '') as valeurs_renseignees
    from toutes_colonnes
    group by nom_table, colonne
),

quarantaine as (
    select 'int_creances' as nom_table, count(*) as lignes_quarantaine from quarantaine.creances
    union all
    select 'int_encaissements' as nom_table, count(*) from quarantaine.encaissements
    union all
    select 'int_factures' as nom_table, count(*) from quarantaine.factures
    union all
    select 'int_lignes_facture' as nom_table, count(*) from quarantaine.lignes_facture
    union all
    select 'int_mouvements' as nom_table, count(*) from quarantaine.mouvements
    union all
    select 'int_passages' as nom_table, count(*) from quarantaine.passages
    union all
    select 'int_passages_urgences' as nom_table, count(*) from quarantaine.passages_urgences
    union all
    select 'int_patients' as nom_table, count(*) from quarantaine.patients
    union all
    select 'int_prises_en_charge' as nom_table, count(*) from quarantaine.prises_en_charge
    union all
    select 'int_relances' as nom_table, count(*) from quarantaine.relances
    union all
    select 'int_rendez_vous' as nom_table, count(*) from quarantaine.rendez_vous
)

select
    par_colonne.nom_table,
    par_colonne.colonne,
    par_colonne.lignes_examinees,
    par_colonne.valeurs_renseignees,
    par_colonne.valeurs_renseignees::numeric / par_colonne.lignes_examinees as taux_completude,
    quarantaine.lignes_quarantaine,
    quarantaine.lignes_quarantaine::numeric
    / (par_colonne.lignes_examinees + quarantaine.lignes_quarantaine) as taux_quarantaine
from par_colonne
inner join quarantaine on par_colonne.nom_table = quarantaine.nom_table
