-- models/analytics/facts/fact_order_items.sql
-- Grain: one row per order line item.
-- Incremental merge on surrogate_key.
-- Partitioned by order_date, clustered by product_id and category.

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
        cluster_by=['product_id', 'category'],
        tags=['facts', 'incremental']
    )
}}

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select
        order_id,
        customer_id,
        order_date,
        order_status,
        order_channel,
        is_delivered
    from {{ ref('int_orders__basket_metrics') }}

    {% if is_incremental() %}
    where order_date >= date_sub(current_date(), interval 3 day)
    {% endif %}
),

products as (
    select
        product_id,
        category,
        subcategory,
        brand
    from {{ ref('stg_products') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['i.order_item_id']) }} as surrogate_key,

        -- keys
        i.order_item_id,
        i.order_id,
        o.customer_id,
        i.product_id,

        -- product context
        p.category,
        p.subcategory,
        p.brand,

        -- order context
        o.order_date,
        o.order_status,
        o.order_channel,
        o.is_delivered,

        -- line metrics
        i.quantity,
        i.unit_price_gbp,
        i.discount_amount_gbp,
        i.line_total_gbp,
        i.is_substituted,
        i.substituted_product_id,

        -- audit
        i.refreshed_at,
        current_timestamp() as dbt_updated_at

    from order_items as i
    inner join orders as o on i.order_id = o.order_id
    left join products as p on i.product_id = p.product_id
)

select * from final
