{#
    Couche intermediate de source.passages : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_passage,
    n_ipp,
    type_passage,
    service,
    activite,
    n_rdv,
    mode_prise_en_charge,
    {{ convertir_horodatage('date_heure_entree') }} as date_heure_entree,
    {{ convertir_horodatage('date_heure_sortie') }} as date_heure_sortie,
    medecin,
    cree_par,
    {{ convertir_horodatage('date_creation') }} as date_creation,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'passages') }}
