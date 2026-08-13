{#
    Conservation des lignes : le nombre de lignes du modèle doit égaler celui de la relation
    de comparaison (sa table source). Deux sous-requêtes indépendantes, jamais un littéral de
    volumétrie -- vaut aussi bien sur un sous-ensemble de 3 mois que sur le scénario complet.
    Le test dbt échoue quand la requête rend des lignes : ici, exactement une ligne si les
    deux décomptes diffèrent, aucune sinon.
#}
{% test meme_decompte_que_la_source(model, compare_model) %}

with decompte_modele as (
    select count(*) as n from {{ model }}
),

decompte_source as (
    select count(*) as n from {{ compare_model }}
)

select
    decompte_modele.n as decompte_modele,
    decompte_source.n as decompte_source
from decompte_modele
cross join decompte_source
where decompte_modele.n != decompte_source.n

{% endtest %}
