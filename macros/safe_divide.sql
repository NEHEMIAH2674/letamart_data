-- macros/safe_divide.sql
-- Safe division that returns null instead of error when dividing by zero.
-- Usage: {{ safe_divide('total_revenue', 'total_orders') }}

{% macro safe_divide(numerator, denominator) %}
    case
        when {{ denominator }} = 0 or {{ denominator }} is null
            then null
        else {{ numerator }} / {{ denominator }}
    end
{% endmacro %}
