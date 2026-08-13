{#
    Couche intermediate de source.encaissements : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_encaissement,
    n_facture,
    {{ convertir_horodatage('date_encaissement') }} as date_encaissement,
    mode_reglement,
    {{ convertir_numerique('montant') }} as montant,
    regisseur,
    {{ convertir_booleen('billet_sortie_delivre') }} as billet_sortie_delivre,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'encaissements') }}
