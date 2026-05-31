-- macros/generate_surrogate_key.sql
-- Wrapper around dbt_utils.generate_surrogate_key for consistency.
-- Ensures all surrogate keys in the project use the same hashing approach.
-- Usage: {{ generate_surrogate_key(['order_id', 'product_id']) }}

{% macro generate_surrogate_key(field_list) %}
    {{ dbt_utils.generate_surrogate_key(field_list) }}
{% endmacro %}
