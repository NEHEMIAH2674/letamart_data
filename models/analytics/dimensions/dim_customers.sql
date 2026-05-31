-- models/analytics/dimensions/dim_customers.sql
-- SCD Type 1: full refresh on every daily run.
-- One row per customer with LTV, RFM segment and value band.

{{
    config(
        materialized='table',
        cluster_by=['loyalty_tier', 'customer_segment'],
        tags=['dimensions']
    )
}}

with customers as (
    select * from {{ ref('int_customers__order_metrics') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,

        -- keys
        customer_id,

        -- attributes
        email,
        first_name,
        last_name,
        concat(first_name, ' ', last_name) as full_name,
        loyalty_tier,
        postcode,
        registered_at,
        cast(registered_at as date) as registration_date,
        is_active,
        days_since_registration,

        -- order behaviour
        has_ordered,
        total_orders,
        orders_this_year,
        lifetime_value_gbp,
        avg_order_value_gbp,
        first_order_date,
        last_order_date,
        days_since_last_order,
        promo_orders_count,
        lifetime_discount_gbp,

        -- segmentation
        customer_segment,

        -- value banding
        case
            when lifetime_value_gbp >= 2000 then 'high'
            when lifetime_value_gbp >= 500 then 'mid'
            when lifetime_value_gbp > 0 then 'low'
            else 'none'
        end as value_band,

        -- audit
        refreshed_at,
        current_timestamp() as dbt_updated_at

    from customers
)

select * from final
