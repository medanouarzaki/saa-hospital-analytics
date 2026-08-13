{#
    Un passage d'urgence par ligne, clé n_passage (unique, mesurée sans doublon sur
    int_passages_urgences). Cet espace de clés est le MÊME que celui de fct_passage
    (int_passages_urgences.n_passage mesuré sous-ensemble strict de
    int_passages.n_passage) : la relation vers fct_passage porte sur n_passage
    directement.

    delai_pec_minutes : aucune colonne brute dans le registre des champs (grandeur
    calculée) ; unité alignée sur generator/config/urgences.yml::delai_pec_par_niveau
    (« minutes, cible de delai avant prise en charge medicale par niveau de tri »).

    service_orientation mesuré très faiblement renseigné (5,88%) : aucun test de
    non-nullité ne porte dessus ; le test relationships vers dim_service, dont la
    macro exclut nativement les valeurs NULL du côté enfant (vérifié dans
    dbt/include/global_project/macros/generic_test_sql/relationships.sql), ne porte
    donc que sur les valeurs effectivement renseignées sans filtre additionnel.
#}

select
    u.n_passage,
    u.n_ipp,
    d.valide_de as patient_valide_de,
    u.date_heure_arrivee,
    u.date_heure_arrivee::date as date_arrivee,
    u.date_heure_pec_medicale,
    u.date_heure_sortie,
    nullif(u.mode_arrivee, '') as mode_arrivee,
    nullif(u.motif_recours, '') as motif_recours,
    nullif(u.niveau_tri, '') as niveau_tri,
    extract(epoch from (u.date_heure_pec_medicale - u.date_heure_arrivee)) / 60.0 as delai_pec_minutes,
    extract(epoch from (u.date_heure_sortie - u.date_heure_arrivee)) / 60.0 as duree_minutes,
    nullif(u.orientation_sortie, '') as orientation_sortie,
    nullif(u.service_orientation, '') as code_service_orientation
from {{ ref('int_passages_urgences') }} as u
left join {{ ref('dim_patient') }} as d
    on
        u.n_ipp = d.n_ipp
        and u.date_heure_arrivee::date >= d.valide_de
        and (u.date_heure_arrivee::date < d.valide_jusqu_a or d.valide_jusqu_a is null)
