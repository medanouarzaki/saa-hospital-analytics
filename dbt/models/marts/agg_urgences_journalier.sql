{#
    Une ligne par jour d'arrivée et niveau de tri, agrégée depuis fct_passage_urgence.

    Ventilation de l'orientation de sortie en quatre décomptes, construite depuis
    generator/config/nomenclatures_clinique.yml::nomenclature_orientation_sortie
    (cinq codes : RD, HO, TR, SC, DC -- cf. rapport de ce lot) :
      - n_retour_domicile   : orientation_sortie = 'RD'
      - n_hospitalisation   : orientation_sortie = 'HO'
      - n_transfert         : orientation_sortie = 'TR'
      - n_autre_orientation : orientation_sortie in ('SC', 'DC') -- sortie contre
        avis médical et décès, regroupées faute de catégorie dédiée demandée.
    Les quatre décomptes somment exactement à nb_passages (vérifié par
    agg_urgences_journalier_coherence) car orientation_sortie est intégralement
    renseignée sur fct_passage_urgence (mesurée 100% aux lots précédents) et les
    cinq codes couvrent la totalité de la nomenclature.
#}

select
    date_arrivee as jour,
    niveau_tri,
    count(*) as nb_passages,
    count(distinct n_ipp) as nb_patients_distincts,
    percentile_cont(0.5) within group (order by delai_pec_minutes) as mediane_delai_pec_minutes,
    percentile_cont(0.9) within group (order by delai_pec_minutes) as p90_delai_pec_minutes,
    percentile_cont(0.5) within group (order by duree_minutes) as mediane_duree_minutes,
    count(*) filter (where orientation_sortie = 'RD') as n_retour_domicile,
    count(*) filter (where orientation_sortie = 'HO') as n_hospitalisation,
    count(*) filter (where orientation_sortie = 'TR') as n_transfert,
    count(*) filter (where orientation_sortie in ('SC', 'DC')) as n_autre_orientation
from {{ ref('fct_passage_urgence') }}
group by date_arrivee, niveau_tri
