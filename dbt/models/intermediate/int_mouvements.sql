{#
    Couche intermediate de source.mouvements : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_sejour,
    n_ipp,
    {{ convertir_horodatage('date_heure_admission') }} as date_heure_admission,
    mode_admission,
    service_accueil,
    lit,
    n_mutation,
    service_origine,
    service_destination,
    {{ convertir_horodatage('date_heure_mutation') }} as date_heure_mutation,
    {{ convertir_horodatage('date_heure_sortie') }} as date_heure_sortie,
    mode_sortie,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'mouvements') }}
