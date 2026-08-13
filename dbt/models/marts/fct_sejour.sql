{#
    Un séjour par ligne, clé n_sejour, agrégé depuis int_mouvements (une ligne par
    mouvement -- admission, mutation facultative, sortie facultative -- structure
    mesurée entièrement déterministe : exactement une ligne d'admission par séjour,
    au plus une ligne de mutation, au plus une ligne de sortie, aucun séjour à
    plusieurs services d'accueil distincts).

    service_accueil et date_heure_admission n'apparaissent que sur la ligne
    d'admission (mesuré), service_origine/service_destination/date_heure_mutation
    que sur la ligne de mutation, date_heure_sortie/mode_sortie que sur la ligne de
    sortie : un simple max() par colonne suffit, sauf pour lit_admission (le lit est
    renseigné à la fois sur la ligne d'admission et sur la ligne de mutation avec
    deux valeurs différentes), isolé par filtre sur la présence de service_accueil.

    service_sortie : dérivé -- service_destination de la ligne de mutation quand
    elle existe, service_accueil sinon (aucune mutation, le patient sort du service
    où il a été accueilli).

    duree_jours : en jours, pour que la durée moyenne de séjour recalculée depuis ce
    fait soit directement comparable à generator/config/volumetrie.yml::dms_publie
    (paramètre en jours).
#}

with sejours as (
    select
        n_sejour,
        min(n_ipp) as n_ipp,
        max(date_heure_admission) as date_heure_admission,
        max(nullif(mode_admission, '')) as mode_admission,
        max(nullif(service_accueil, '')) as service_accueil,
        max(nullif(lit, '')) filter (where nullif(service_accueil, '') is not null) as lit_admission,
        max(nullif(service_origine, '')) as service_origine,
        max(nullif(service_destination, '')) as service_destination,
        max(date_heure_mutation) as date_heure_mutation,
        max(date_heure_sortie) as date_heure_sortie,
        max(nullif(mode_sortie, '')) as mode_sortie,
        count(*) as nb_lignes_mouvement
    from {{ ref('int_mouvements') }}
    group by n_sejour
)

select
    s.n_sejour,
    s.n_ipp,
    d.valide_de as patient_valide_de,
    s.date_heure_admission,
    s.date_heure_admission::date as jour_admission,
    s.mode_admission,
    s.service_accueil,
    s.lit_admission,
    s.date_heure_mutation,
    s.service_origine,
    s.service_destination,
    s.date_heure_sortie,
    s.date_heure_sortie::date as jour_sortie,
    s.mode_sortie,
    s.nb_lignes_mouvement,
    s.service_origine is not null as a_une_mutation,
    s.date_heure_sortie is not null as est_clos,
    coalesce(s.service_destination, s.service_accueil) as service_sortie,
    case
        when s.date_heure_sortie is not null
            then extract(epoch from (s.date_heure_sortie - s.date_heure_admission)) / 86400.0
    end as duree_jours
from sejours as s
left join {{ ref('dim_patient') }} as d
    on
        s.n_ipp = d.n_ipp
        and s.date_heure_admission::date >= d.valide_de
        and (s.date_heure_admission::date < d.valide_jusqu_a or d.valide_jusqu_a is null)
