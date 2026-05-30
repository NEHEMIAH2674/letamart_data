-- models/intermediate/int_orders__basket_metrics.sql
-- Joins orders → order_items → promotions.
-- Produces one row per order with basket-level aggregates.
-- Ephemeral: no BigQuery table created, compiled inline by downstream models.

with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

promotions as (
    select * from {{ ref('stg_promotions') }}
),

basket_agg as (
    select
        order_id,
        count(*) as item_line_count,
        sum(quantity) as total_units,
        sum(line_total_gbp) as basket_value_gbp,
        sum(discount_amount_gbp) as total_discount_gbp,
        countif(is_substituted) as substituted_line_count,
        sum(line_total_gbp)
        + sum(coalesce(discount_amount_gbp, 0)) as gross_basket_gbp

    from order_items
    group by 1
),

order_basket_metrics as (
    select
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_channel,
        o.order_created_at,
        o.delivery_slot_start_at,
        o.delivery_slot_end_at,
        o.promo_code,
        o.refreshed_at,

        -- basket metrics
        b.item_line_count,
        b.total_units,
        b.basket_value_gbp,
        b.total_discount_gbp,
        b.gross_basket_gbp,
        b.substituted_line_count,

        -- promo info
        p.promo_type,
        p.discount_value as promo_discount_value,

        -- flags
        o.order_status = 'delivered' as is_delivered,
        o.order_status = 'cancelled' as is_cancelled,
        o.order_status = 'returned' as is_returned,
        p.promo_id is not null as has_promo,

        -- date parts for partitioning downstream
        date(o.order_created_at) as order_date,
        extract(year from o.order_created_at) as order_year,
        extract(month from o.order_created_at) as order_month,
        extract(week from o.order_created_at) as order_week,
        extract(hour from o.order_created_at) as order_hour

    from orders as o
    left join basket_agg as b on o.order_id = b.order_id
    left join promotions as p on o.promo_code = p.promo_code
)

select * from order_basket_metrics
