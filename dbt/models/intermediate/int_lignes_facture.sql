{#
    Couche intermediate de source.lignes_facture : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_facture,
    {{ convertir_numerique('n_ligne') }} as n_ligne,
    code_acte,
    libelle_acte,
    lettre_cle,
    {{ convertir_numerique('coefficient') }} as coefficient,
    {{ convertir_numerique('quantite') }} as quantite,
    {{ convertir_numerique('tarif_unitaire') }} as tarif_unitaire,
    {{ convertir_numerique('montant') }} as montant,
    service_executant,
    {{ convertir_date('date_acte') }} as date_acte,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'lignes_facture') }}
