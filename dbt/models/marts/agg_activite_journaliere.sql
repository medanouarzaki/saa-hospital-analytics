{#
    Une ligne par jour, type d'événement, service et activité. service et activite
    sont NULS pour les familles qui n'en portent pas -- NUL signifie « non
    applicable » (aucune colonne de cette nature n'existe pour cette famille dans le
    fait source), jamais « inconnu » (une valeur inconnue mais applicable resterait
    une chaîne vide convertie en NULL par la couche intermediate, indiscernable ici
    -- mesuré : aucune des quatre familles ne présente ce cas pour les colonnes
    utilisées).

    Quatre familles, quatre valeurs de type_evenement, sans chevauchement possible
    (chaque ligne du fait source alimente exactement une famille) :
      - RENDEZ_VOUS : fct_rendez_vous, jour = date_rendez_vous, activite =
        code_activite, service NUL (aucune colonne de service dans ce fait, mesuré).
      - PASSAGE_C / PASSAGE_H / PASSAGE_U : fct_passage, jour = date_entree, ventilé
        par type_passage (mesuré : chaque type porte exactement un service, jamais
        nul -- C→CE, H→HM, U→UR), activite = code_activite (renseignée seulement
        pour les consultations, NULE pour H et U -- mesuré aux lots précédents).
      - ADMISSION_SEJOUR : fct_sejour, jour = jour_admission, service =
        service_accueil, pour l'ensemble des séjours (clos ou non).
      - SORTIE_SEJOUR : fct_sejour, jour = jour_sortie, service = service_sortie,
        pour les SEULS séjours clos (est_clos) -- un séjour non clos n'a pas de jour
        de sortie.
#}

with evenements as (
    select
        date_rendez_vous as jour,
        'RENDEZ_VOUS' as type_evenement,
        cast(null as text) as service,
        code_activite as activite,
        n_ipp
    from {{ ref('fct_rendez_vous') }}

    union all

    select
        date_entree as jour,
        'PASSAGE_' || type_passage as type_evenement,
        code_service as service,
        code_activite as activite,
        n_ipp
    from {{ ref('fct_passage') }}

    union all

    select
        jour_admission as jour,
        'ADMISSION_SEJOUR' as type_evenement,
        service_accueil as service,
        cast(null as text) as activite,
        n_ipp
    from {{ ref('fct_sejour') }}

    union all

    select
        jour_sortie as jour,
        'SORTIE_SEJOUR' as type_evenement,
        service_sortie as service,
        cast(null as text) as activite,
        n_ipp
    from {{ ref('fct_sejour') }}
    where est_clos
)

select
    jour,
    type_evenement,
    service,
    activite,
    count(*) as nb_evenements,
    count(distinct n_ipp) as nb_patients_distincts
from evenements
group by jour, type_evenement, service, activite
