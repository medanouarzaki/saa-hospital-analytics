{#
    Non-chevauchement des intervalles : deux versions d'un même n_ipp dont les intervalles
    [valide_de, valide_jusqu_a) se recouvrent rendent une ligne. Borne NULL = infini ouvert
    (deux versions courantes du même n_ipp -- qui ne devraient jamais exister -- se
    recouvriraient TOUJOURS) : coalesce sur une date sentinelle très lointaine porte cette
    sémantique sans dépendre d'un littéral d'infini du moteur.
#}

with a as (
    select
        n_ipp,
        valide_de,
        valide_jusqu_a
    from {{ ref('dim_patient') }}
),

b as (
    select
        n_ipp,
        valide_de,
        valide_jusqu_a
    from {{ ref('dim_patient') }}
)

select
    a.n_ipp,
    a.valide_de as a_valide_de,
    a.valide_jusqu_a as a_valide_jusqu_a,
    b.valide_de as b_valide_de,
    b.valide_jusqu_a as b_valide_jusqu_a
from a
inner join b
    on
        a.n_ipp = b.n_ipp
        and a.valide_de < b.valide_de
where
    a.valide_de < coalesce(b.valide_jusqu_a, date '9999-12-31')
    and b.valide_de < coalesce(a.valide_jusqu_a, date '9999-12-31')
