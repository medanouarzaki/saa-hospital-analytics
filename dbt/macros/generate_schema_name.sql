{#
    Surcharge du macro global generate_schema_name (dbt-core, macros/get_custom_name/
    get_custom_schema.sql : "This macro can be overriden in projects to define different
    semantics for rendering a schema name"). Le comportement par défaut concatène le schéma
    cible et le schéma personnalisé (`<cible>_<custom>` -- mesuré : un modèle configuré
    `schema: intermediate` sur une cible `intermediate` atterrissait dans
    `intermediate_intermediate`). Ce projet utilise directement le nom de schéma personnalisé
    quand il est fourni, sans préfixe, pour obtenir exactement `intermediate`/`marts`.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
