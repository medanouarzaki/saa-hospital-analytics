{#
    Conversion sans perte : pour une colonne convertie, le nombre de valeurs source non
    vides doit égaler le nombre de valeurs converties non nulles -- deux décomptes
    indépendants, chacun sur sa propre relation. Une conversion qui échoue silencieusement
    (format inattendu -> NULL) ferait diverger les deux décomptes.
#}
{% test conversion_sans_perte(model, column_name, source_relation, source_column) %}

with source_non_vide as (
    select count(*) as n
    from {{ source_relation }}
    where nullif({{ source_column }}, '') is not null
),

convertie_non_nulle as (
    select count(*) as n
    from {{ model }}
    where {{ column_name }} is not null
)

select
    source_non_vide.n as source_non_vide,
    convertie_non_nulle.n as convertie_non_nulle
from source_non_vide
cross join convertie_non_nulle
where source_non_vide.n != convertie_non_nulle.n

{% endtest %}
