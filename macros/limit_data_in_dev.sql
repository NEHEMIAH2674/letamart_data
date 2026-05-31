-- macros/limit_data_in_dev.sql
-- Limits data volume in dev target to reduce BigQuery costs during development.
-- Usage: {{ limit_data_in_dev('order_created_at', 90) }}
-- In dev: adds WHERE clause for last N days
-- In prod: no filter applied

{% macro limit_data_in_dev(date_column, days=90) %}
    {% if target.name == 'dev' %}
        where {{ date_column }} >= date_sub(current_date(), interval {{ days }} day)
    {% endif %}
{% endmacro %}
