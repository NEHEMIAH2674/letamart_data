-- models/intermediate/int_product_performance.sql
-- Product-grain: revenue, margin, sell-through, substitution rate.

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select
        order_id,
        order_date,
        order_status,
        is_delivered
    from {{ ref('int_orders__basket_metrics') }}
    where is_delivered = true
),

products as (
    select * from {{ ref('stg_products') }}
),

inventory as (
    select
        product_id,
        units_available,
        is_below_reorder_point
    from {{ ref('stg_inventory') }}
    qualify row_number() over (
        partition by product_id
        order by snapshot_date desc
    ) = 1
),

product_sales as (
    select
        i.product_id,
        count(distinct o.order_id) as orders_containing_product,
        sum(i.quantity) as total_units_sold,
        sum(i.line_total_gbp) as total_revenue_gbp,
        sum(i.discount_amount_gbp) as total_discount_gbp,
        avg(i.unit_price_gbp) as avg_selling_price_gbp,
        countif(i.is_substituted) as times_substituted_away

    from order_items as i
    inner join orders as o on i.order_id = o.order_id
    group by 1
),

joined as (
    select
        p.product_id,
        p.product_name,
        p.sku,
        p.category,
        p.subcategory,
        p.brand,
        p.cost_price_gbp,
        p.rrp_gbp,
        p.is_active,
        p.is_age_restricted,
        p.refreshed_at,

        -- sales metrics
        inv.units_available,
        inv.is_below_reorder_point,
        coalesce(s.orders_containing_product, 0) as orders_containing_product,
        coalesce(s.total_units_sold, 0) as total_units_sold,
        coalesce(s.total_revenue_gbp, 0) as total_revenue_gbp,
        coalesce(s.total_discount_gbp, 0) as total_discount_gbp,

        -- margin
        coalesce(s.avg_selling_price_gbp, 0) as avg_selling_price_gbp,

        coalesce(s.times_substituted_away, 0) as times_substituted_away,

        -- inventory
        coalesce(s.total_revenue_gbp, 0)
        - (coalesce(s.total_units_sold, 0) * p.cost_price_gbp)
            as gross_margin_gbp,
        case
            when coalesce(s.total_revenue_gbp, 0) = 0 then null
            else round(
                (
                    coalesce(s.total_revenue_gbp, 0)
                    - (coalesce(s.total_units_sold, 0) * p.cost_price_gbp)
                )
                / s.total_revenue_gbp * 100, 2
            )
        end as gross_margin_pct

    from products as p
    left join product_sales as s on p.product_id = s.product_id
    left join inventory as inv on products.product_id = inv.product_id
)

select * from joined
