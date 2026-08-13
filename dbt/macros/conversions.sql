{#
    Macros de conversion typée de la couche source (intégralement text) vers des types
    PostgreSQL natifs. Fondées sur des mesures, pas des suppositions :
      - la valeur manquante est toujours la chaîne vide, jamais NULL (mesuré sur cinq
        colonnes de trois types en base : zéro NULL partout) ;
      - les dates sont au format MM/DD/YYYY, les horodatages MM/DD/YYYY HH12:MI:SS AM
        (mesuré, zéro valeur non convertible sur les 52 colonnes typées) ;
      - le domaine booléen est exactement {'0', '1', ''} (inventaire exhaustif des neuf
        colonnes booléennes du registre, aucune autre valeur observée).
    Chaque macro reste une expression pure (pas de sous-requête), pour composer directement
    dans la liste de colonnes d'un `select`.
#}

{% macro convertir_date(colonne) %}
    to_date(nullif({{ colonne }}, ''), 'MM/DD/YYYY')
{% endmacro %}

{% macro convertir_horodatage(colonne) %}
    to_timestamp(nullif({{ colonne }}, ''), 'MM/DD/YYYY HH12:MI:SS AM')
{% endmacro %}

{% macro convertir_numerique(colonne) %}
    nullif({{ colonne }}, '')::numeric
{% endmacro %}

{% macro convertir_booleen(colonne) %}
    case nullif({{ colonne }}, '')
        when '1' then true
        when '0' then false
        else null
    end
{% endmacro %}
