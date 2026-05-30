-- models/intermediate/int_customer_orders.sql
-- Customer-grain aggregation: lifetime value, frequency, recency.
-- Feeds dim_customers and reporting_customer_ltv.

with orders as (
    select * from {{ ref('int_orders__basket_metrics') }}
    where is_delivered = true
),

customers as (
    select * from {{ ref('stg_customers') }}
),

order_agg as (
    select
        customer_id,
        count(*) as total_orders,
        countif(order_year = extract(year from current_date()))
            as orders_this_year,
        sum(basket_value_gbp) as lifetime_value_gbp,
        avg(basket_value_gbp) as avg_order_value_gbp,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        date_diff(current_date(), max(order_date), day) as days_since_last_order,
        countif(has_promo) as promo_orders_count,
        sum(total_discount_gbp) as lifetime_discount_gbp

    from orders
    group by 1
),

joined as (
    select
        c.customer_id,
        c.email,
        c.first_name,
        c.last_name,
        c.loyalty_tier,
        c.registered_at,
        c.postcode,
        c.is_active,
        c.days_since_registration,
        c.refreshed_at,

        -- order metrics
        a.first_order_date,
        a.last_order_date,
        coalesce(a.total_orders, 0) as total_orders,
        coalesce(a.orders_this_year, 0) as orders_this_year,
        coalesce(a.lifetime_value_gbp, 0) as lifetime_value_gbp,
        coalesce(a.avg_order_value_gbp, 0) as avg_order_value_gbp,
        coalesce(a.days_since_last_order, 9999) as days_since_last_order,
        coalesce(a.promo_orders_count, 0) as promo_orders_count,
        coalesce(a.lifetime_discount_gbp, 0) as lifetime_discount_gbp,

        -- RFM segmentation
        case
            when a.days_since_last_order <= 30 then 'active'
            when a.days_since_last_order <= 90 then 'at_risk'
            when a.days_since_last_order <= 180 then 'lapsing'
            when a.total_orders is null then 'never_ordered'
            else 'churned'
        end as customer_segment,

        a.total_orders is not null as has_ordered

    from customers as c
    left join order_agg as a on c.customer_id = a.customer_id
)

select * from joined
