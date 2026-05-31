-- macros/get_revenue_metrics.sql
-- Reusable revenue aggregation block for reporting models.
-- Usage: {{ get_revenue_metrics('basket_value_gbp', 'total_discount_gbp') }}

{% macro get_revenue_metrics(gross_col, discount_col) %}
    sum({{ gross_col }})                                        as gross_revenue_gbp,
    sum({{ discount_col }})                                     as total_discount_gbp,
    sum({{ gross_col }}) - sum({{ discount_col }})              as net_revenue_gbp,
    avg({{ gross_col }})                                        as avg_basket_gbp,
    safe_divide(
        sum({{ discount_col }}),
        sum({{ gross_col }})
    )                                                           as discount_rate
{% endmacro %}
