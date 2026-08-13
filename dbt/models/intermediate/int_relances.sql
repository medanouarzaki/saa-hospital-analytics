{#
    Couche intermediate de source.relances : les colonnes du registre, chaque colonne
    typee passee par la macro de conversion correspondant a son type_metier ; les
    colonnes code/texte reprises telles quelles. Correspondance colonne -> macro
    generee par script depuis le registre, pas ecrite de memoire.
#}

select
    n_relance,
    n_creance,
    {{ convertir_date('date_relance') }} as date_relance,
    canal,
    resultat,
    {{ convertir_date('date_extraction') }} as date_extraction
from {{ source('source', 'relances') }}
