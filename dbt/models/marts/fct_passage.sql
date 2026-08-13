{#
    Un passage par ligne, clé n_passage (unique, mesurée sans doublon sur
    int_passages). Table pivot couvrant TOUS les types de passage (C, H, U) — c'est
    la cible à laquelle n_episode des factures et prises en charge se raccorde à
    100% pour les trois valeurs de type_episode, non restreinte ici.

    code_activite n'est renseignée que pour les passages de consultation (type_passage
    = 'C', mesuré 100% sur ce sous-ensemble, 0% sur H et U) : aucun test de
    non-nullité ne porte dessus.

    n_rdv brut est renseigné sur toutes les lignes mais ne se raccorde
    effectivement à un rendez-vous que pour une partie d'entre elles (mesuré :
    décompte de raccordement effectif = décompte de rendez-vous honorés). n_rdv_resolu
    n'expose donc la valeur QUE lorsque le raccordement existe réellement,
    NULL sinon — c'est cette colonne, pas la colonne brute, qui porte la relation
    vers fct_rendez_vous.

    duree_minutes : aucune colonne brute de durée dans le registre des champs pour
    cette table (grandeur calculée) ; unité alignée sur
    generator/config/passages.yml::duree_mediane_minutes_par_categorie (minutes).
#}

select
    p.n_passage,
    p.n_ipp,
    d.valide_de as patient_valide_de,
    p.type_passage,
    nullif(p.service, '') as code_service,
    nullif(p.activite, '') as code_activite,
    case
        when
            exists (
                select 1 from {{ ref('int_rendez_vous') }} as r
                where r.n_rdv = p.n_rdv
            )
            then nullif(p.n_rdv, '')
    end as n_rdv_resolu,
    p.date_heure_entree,
    p.date_heure_entree::date as date_entree,
    p.date_heure_sortie,
    extract(epoch from (p.date_heure_sortie - p.date_heure_entree)) / 60.0 as duree_minutes,
    nullif(p.mode_prise_en_charge, '') as mode_prise_en_charge,
    nullif(p.medecin, '') as medecin,
    nullif(p.cree_par, '') as agent_creation
from {{ ref('int_passages') }} as p
left join {{ ref('dim_patient') }} as d
    on
        p.n_ipp = d.n_ipp
        and p.date_heure_entree::date >= d.valide_de
        and (p.date_heure_entree::date < d.valide_jusqu_a or d.valide_jusqu_a is null)
