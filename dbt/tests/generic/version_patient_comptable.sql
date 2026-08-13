{#
    Une ligne de fait dont patient_valide_de est nulle n'est admissible que dans deux
    cas, tous deux prouvables depuis dim_patient seule : son n_ipp n'apparaît dans
    aucune ligne de dim_patient, ou son jour d'événement précède le plus petit
    valide_de de ce n_ipp. Toute autre ligne non résolue (trou de continuité, version
    terminale non courante, erreur de bornes dans le modèle de fait) fait rougir ce
    test.

    Mesuré sur deux générations canoniques (base complète et sous-ensemble de trois
    mois) et sept populations d'événements : seules ces deux causes de
    non-résolution ont été observées, jamais de troisième.
#}
{% test version_patient_comptable(model, jour_column) %}

with bornes as (
    select n_ipp, min(valide_de) as premiere_version
    from {{ ref('dim_patient') }}
    group by n_ipp
),

non_resolues as (
    select m.n_ipp, m.{{ jour_column }} as jour
    from {{ model }} m
    where m.patient_valide_de is null
)

select nr.n_ipp, nr.jour
from non_resolues nr
left join bornes b on b.n_ipp = nr.n_ipp
where
    b.n_ipp is not null
    and not (nr.jour < b.premiere_version)

{% endtest %}
