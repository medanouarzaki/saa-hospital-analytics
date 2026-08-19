{#
    Couverture des événements : aucune date d'événement des vues intermediate n'est absente de
    dim_date. Liste des 34 colonnes d'événement générée par script depuis le registre (34
    colonnes date/horodatage, moins les quatre colonnes d'état civil de patients dont le minimum
    mesuré est antérieur à 2023-08-01 : date_naissance, date_photo, date_attribution,
    date_inscription, exclusion mesuree). La liste est collée
    ici, statique ; le script n'est que l'outil de génération, pas une dépendance du test.
#}

with evenements as (

    select date_extraction::date as jour from {{ ref('int_creances') }}
    where date_extraction is not null

    union all

    select date_naissance_creance::date as jour from {{ ref('int_creances') }}
    where date_naissance_creance is not null

    union all

    select date_encaissement::date as jour from {{ ref('int_encaissements') }}
    where date_encaissement is not null

    union all

    select date_extraction::date as jour from {{ ref('int_encaissements') }}
    where date_extraction is not null

    union all

    select date_creation::date as jour from {{ ref('int_factures') }}
    where date_creation is not null

    union all

    select date_extraction::date as jour from {{ ref('int_factures') }}
    where date_extraction is not null

    union all

    select date_facture::date as jour from {{ ref('int_factures') }}
    where date_facture is not null

    union all

    select date_acte::date as jour from {{ ref('int_lignes_facture') }}
    where date_acte is not null

    union all

    select date_extraction::date as jour from {{ ref('int_lignes_facture') }}
    where date_extraction is not null

    union all

    select date_extraction::date as jour from {{ ref('int_mouvements') }}
    where date_extraction is not null

    union all

    select date_heure_admission::date as jour from {{ ref('int_mouvements') }}
    where date_heure_admission is not null

    union all

    select date_heure_mutation::date as jour from {{ ref('int_mouvements') }}
    where date_heure_mutation is not null

    union all

    select date_heure_sortie::date as jour from {{ ref('int_mouvements') }}
    where date_heure_sortie is not null

    union all

    select date_creation::date as jour from {{ ref('int_passages') }}
    where date_creation is not null

    union all

    select date_extraction::date as jour from {{ ref('int_passages') }}
    where date_extraction is not null

    union all

    select date_heure_entree::date as jour from {{ ref('int_passages') }}
    where date_heure_entree is not null

    union all

    select date_heure_sortie::date as jour from {{ ref('int_passages') }}
    where date_heure_sortie is not null

    union all

    select date_extraction::date as jour from {{ ref('int_passages_urgences') }}
    where date_extraction is not null

    union all

    select date_heure_arrivee::date as jour from {{ ref('int_passages_urgences') }}
    where date_heure_arrivee is not null

    union all

    select date_heure_pec_medicale::date as jour
    from {{ ref('int_passages_urgences') }}
    where date_heure_pec_medicale is not null

    union all

    select date_heure_sortie::date as jour from {{ ref('int_passages_urgences') }}
    where date_heure_sortie is not null

    union all

    select date_extraction::date as jour from {{ ref('int_patients') }}
    where date_extraction is not null

    union all

    select date_modification::date as jour from {{ ref('int_patients') }}
    where date_modification is not null

    union all

    select date_extraction::date as jour from {{ ref('int_prises_en_charge') }}
    where date_extraction is not null

    union all

    select date_verification::date as jour from {{ ref('int_prises_en_charge') }}
    where date_verification is not null

    union all

    select date_extraction::date as jour from {{ ref('int_relances') }}
    where date_extraction is not null

    union all

    select date_relance::date as jour from {{ ref('int_relances') }}
    where date_relance is not null

    union all

    select date_annul::date as jour from {{ ref('int_rendez_vous') }}
    where date_annul is not null

    union all

    select date_conf::date as jour from {{ ref('int_rendez_vous') }}
    where date_conf is not null

    union all

    select date_creation::date as jour from {{ ref('int_rendez_vous') }}
    where date_creation is not null

    union all

    select date_extraction::date as jour from {{ ref('int_rendez_vous') }}
    where date_extraction is not null

    union all

    select date_mod::date as jour from {{ ref('int_rendez_vous') }}
    where date_mod is not null

    union all

    select date_reception::date as jour from {{ ref('int_rendez_vous') }}
    where date_reception is not null

    union all

    select date_rendez_vous::date as jour from {{ ref('int_rendez_vous') }}
    where date_rendez_vous is not null

),

jours_dim as (
    select date_jour
    from {{ ref('dim_date') }}
)

select distinct evenements.jour
from evenements
left join jours_dim on evenements.jour = jours_dim.date_jour
where jours_dim.date_jour is null
