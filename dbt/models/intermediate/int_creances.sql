{#
    Couche intermediate de source.creances : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_creance,
    n_facture,
    {{ convertir_date('date_naissance_creance') }} as date_naissance_creance,
    {{ convertir_numerique('montant_du') }} as montant_du,
    {{ convertir_numerique('montant_recouvre') }} as montant_recouvre,
    {{ convertir_numerique('montant_restant') }} as montant_restant,
    type_debiteur,
    motif_non_recouvrement,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'creances') }}
