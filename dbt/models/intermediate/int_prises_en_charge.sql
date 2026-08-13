{#
    Couche intermediate de source.prises_en_charge : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_prise_en_charge,
    n_ipp,
    n_episode,
    type_episode,
    organisme,
    n_assure,
    {{ convertir_horodatage('date_verification') }} as date_verification,
    etat,
    {{ convertir_numerique('taux_prise_en_charge') }} as taux_prise_en_charge,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'prises_en_charge') }}
