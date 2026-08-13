{#
    Un rendez-vous par ligne, clé n_rdv (unique, mesurée sans doublon sur
    int_rendez_vous). patient_valide_de résout la version de dim_patient en
    vigueur au jour du rendez-vous, borne haute exclusive.

    Trois drapeaux d'état couvrent les significations établies par
    generator/config/rendez_vous.yml (code_etat_absence = CO) et
    generator/config/nomenclatures_organisation_activite.yml
    (nomenclature_etat_rendez_vous : HO=Honoré, CO=Confirmé/absence, AN=Annulé,
    EI=En instance) : est_honore, est_absence, est_annule. EI ne correspond à
    aucune des trois significations établies pour ces drapeaux ; il reste
    identifiable par la seule colonne etat, sans drapeau propre.

    duree_minutes : docs/champs/registre_champs.yml, source.rendez_vous.duree,
    « Durée exprimée en minutes ».

    est_patient_adresse : origine = 'AU' (nomenclature_origine, AUTRES HÔPITAUX),
    seul code d'adressage effectivement écrit par generator/rendez_vous.py.

    medecin_ext n'est pas couvert par dim_agent (mesuré : 100% orphelin) — conservé
    comme attribut sans relation, non testé en relationships.
#}

select
    r.n_rdv,
    r.n_ipp,
    d.valide_de as patient_valide_de,
    r.activite as code_activite,
    r.date_rendez_vous::date as date_rendez_vous,
    r.date_creation::date as date_prise,
    r.date_conf::date as date_confirmation,
    r.date_annul::date as date_annulation,
    r.etat,
    r.duree as duree_minutes,
    nullif(r.agenda, '') as code_agenda,
    r.date_rendez_vous::date - r.date_creation::date as delai_obtention_jours,
    (r.date_rendez_vous::date - r.date_creation::date) = 0 as est_jour_meme,
    r.etat = 'HO' as est_honore,
    r.etat = 'CO' as est_absence,
    r.etat = 'AN' as est_annule,
    nullif(r.origine, '') as origine,
    r.origine = 'AU' as est_patient_adresse,
    nullif(r.cree_par, '') as agent_creation,
    nullif(r.modifie_par, '') as agent_modification,
    nullif(r.confirme_par, '') as agent_confirmation,
    nullif(r.annule_par, '') as agent_annulation,
    nullif(r.medecin_ext, '') as medecin_ext
from {{ ref('int_rendez_vous') }} as r
left join {{ ref('dim_patient') }} as d
    on
        r.n_ipp = d.n_ipp
        and r.date_rendez_vous::date >= d.valide_de
        and (r.date_rendez_vous::date < d.valide_jusqu_a or d.valide_jusqu_a is null)
