{#
    Couche intermediate de source.factures : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_facture,
    n_ipp,
    n_episode,
    type_episode,
    code_diagnostic_cim10,
    {{ convertir_date('date_facture') }} as date_facture,
    type_facture,
    service_emetteur,
    etat,
    {{ convertir_numerique('montant_total') }} as montant_total,
    {{ convertir_numerique('part_organisme') }} as part_organisme,
    {{ convertir_numerique('part_patient') }} as part_patient,
    cree_par,
    {{ convertir_horodatage('date_creation') }} as date_creation,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'factures') }}
