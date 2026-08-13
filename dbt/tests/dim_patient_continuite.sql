{#
    Continuité des intervalles : pour toute version non courante, valide_jusqu_a égale
    exactement le valide_de de la version suivante -- aucun trou, aucun recouvrement,
    l'égalité stricte de la convention semi-ouverte.
#}

with ordonne as (
    select
        n_ipp,
        valide_de,
        valide_jusqu_a,
        lead(valide_de) over (partition by n_ipp order by valide_de) as valide_de_suivant
    from {{ ref('dim_patient') }}
)

select
    n_ipp,
    valide_de,
    valide_jusqu_a,
    valide_de_suivant
from ordonne
where
    valide_jusqu_a is not null
    and valide_jusqu_a != valide_de_suivant
