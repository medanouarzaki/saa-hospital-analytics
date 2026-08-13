{#
    Couche intermediate de source.rendez_vous : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_rdv,
    n_ipp,
    agenda,
    activite,
    origine,
    hopital_cs,
    medecin_ext,
    service_ext,
    observations,
    {{ convertir_horodatage('date_rendez_vous') }} as date_rendez_vous,
    {{ convertir_booleen('rdv_supplementaire') }} as rdv_supplementaire,
    type_attention,
    etat,
    {{ convertir_numerique('duree') }} as duree,
    {{ convertir_horodatage('date_reception') }} as date_reception,
    {{ convertir_booleen('imprimer_donnees') }} as imprimer_donnees,
    cree_par,
    {{ convertir_horodatage('date_creation') }} as date_creation,
    modifie_par,
    {{ convertir_horodatage('date_mod') }} as date_mod,
    confirme_par,
    {{ convertir_horodatage('date_conf') }} as date_conf,
    annule_par,
    {{ convertir_horodatage('date_annul') }} as date_annul,
    liste_attente_service,
    liste_attente_agenda,
    liste_attente_activite,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'rendez_vous') }}
