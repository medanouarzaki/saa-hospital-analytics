{#
    Couche intermediate de source.passages_urgences : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_passage,
    n_ipp,
    {{ convertir_horodatage('date_heure_arrivee') }} as date_heure_arrivee,
    mode_arrivee,
    motif_recours,
    niveau_tri,
    {{ convertir_horodatage('date_heure_pec_medicale') }} as date_heure_pec_medicale,
    {{ convertir_horodatage('date_heure_sortie') }} as date_heure_sortie,
    orientation_sortie,
    service_orientation,
    motif_transfert,
    {{ convertir_booleen('consentement_transfert') }} as consentement_transfert,
    {{ convertir_booleen('famille_informee') }} as famille_informee,
    {{ convertir_booleen('inventaire_effets') }} as inventaire_effets,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'passages_urgences') }}
