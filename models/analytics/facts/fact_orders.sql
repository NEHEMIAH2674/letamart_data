-- models/analytics/facts/fact_orders.sql
-- Grain: one row per order.
-- Incremental merge on surrogate_key.
-- Partitioned by order_date, clustered by order_status and order_channel.

{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='surrogate_key',
        partition_by={
            'field': 'order_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        cluster_by=['order_status', 'order_channel'],
        tags=['facts', 'incremental']
    )
}}

with orders as (
    select * from {{ ref('int_orders__basket_metrics') }}

    {% if is_incremental() %}
    where order_date >= date_sub(current_date(), interval 3 day)
    {% endif %}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['order_id']) }} as surrogate_key,

        -- keys
        order_id,
        customer_id,

        -- descriptors
        order_status,
        order_channel,
        promo_code,
        promo_type,

        -- dates
        order_date,
        order_year,
        order_month,
        order_week,
        order_hour,
        order_created_at,
        delivery_slot_start_at,
        delivery_slot_end_at,

        -- basket metrics
        item_line_count,
        total_units,
        basket_value_gbp,
        gross_basket_gbp,
        total_discount_gbp,
        substituted_line_count,

        -- flags
        is_delivered,
        is_cancelled,
        is_returned,
        has_promo,

        -- audit
        refreshed_at,
        current_timestamp() as dbt_updated_at

    from orders
)

select * from final
