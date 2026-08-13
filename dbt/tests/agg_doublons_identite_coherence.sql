{#
    Cohérence de agg_doublons_identite. Quatre propriétés, chacune l'égalité (ou
    l'inégalité bornante) de deux quantités calculées indépendamment, aucun littéral.
#}

with grain_duplique as (
    select
        critere,
        count(*) as n
    from {{ ref('agg_doublons_identite') }}
    group by critere
    having count(*) > 1
),

patients_examines_non_constants as (
    select count(distinct patients_examines) as n from {{ ref('agg_doublons_identite') }}
),

decompte_patients_courants as (
    select count(*) as n from {{ ref('dim_patient') }} where est_courante
),

lignes_borne_groupes_violee as (
    select count(*) as n
    from {{ ref('agg_doublons_identite') }}
    where patients_concernes < 2 * nombre_groupes
),

lignes_borne_taille_max_violee as (
    select count(*) as n
    from {{ ref('agg_doublons_identite') }}
    where taille_plus_grand_groupe > patients_concernes
),

lignes_borne_concernes_violee as (
    select count(*) as n
    from {{ ref('agg_doublons_identite') }}
    where patients_concernes > patients_examines
),

premiere_ligne as (
    select patients_examines as n from {{ ref('agg_doublons_identite') }} limit 1
)

select
    patients_examines_non_constants.n as patients_examines_non_constants,
    premiere_ligne.n as patients_examines,
    decompte_patients_courants.n as decompte_patients_courants,
    lignes_borne_groupes_violee.n as lignes_borne_groupes_violee,
    lignes_borne_taille_max_violee.n as lignes_borne_taille_max_violee,
    lignes_borne_concernes_violee.n as lignes_borne_concernes_violee,
    (select count(*) from grain_duplique) as grain_duplique
from patients_examines_non_constants
cross join premiere_ligne
cross join decompte_patients_courants
cross join lignes_borne_groupes_violee
cross join lignes_borne_taille_max_violee
cross join lignes_borne_concernes_violee
where
    exists (select 1 from grain_duplique)
    or patients_examines_non_constants.n != 1
    or premiere_ligne.n != decompte_patients_courants.n
    or lignes_borne_groupes_violee.n > 0
    or lignes_borne_taille_max_violee.n > 0
    or lignes_borne_concernes_violee.n > 0
