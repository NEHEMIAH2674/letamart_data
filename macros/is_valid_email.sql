-- macros/is_valid_email.sql
-- Returns boolean true if column matches a valid email format.
-- Usage: {{ is_valid_email('email') }}
-- Example test: where not {{ is_valid_email('email') }}

{% macro is_valid_email(column_name) %}
    regexp_contains(
        {{ column_name }},
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
{% endmacro %}
