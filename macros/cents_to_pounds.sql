-- macros/cents_to_pounds.sql
-- Converts integer pence values to decimal GBP.
-- Usage: {{ cents_to_pounds('price_in_pence') }}

{% macro cents_to_pounds(column_name) %}
    round(cast({{ column_name }} as numeric) / 100, 2)
{% endmacro %}
