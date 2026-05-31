-- macros/current_timestamp_utc.sql
-- Returns current timestamp in UTC.
-- Ensures consistent timezone handling across all models.
-- Usage: {{ current_timestamp_utc() }}

{% macro current_timestamp_utc() %}
    timestamp(datetime(current_timestamp(), 'UTC'))
{% endmacro %}
