-- models/analytics/dimensions/dim_products.sql
-- SCD Type 1: full refresh on every daily run.
-- One row per product with performance metrics and inventory status.

{{
    config(
        materialized='table',
        cluster_by=['category', 'subcategory'],
        tags=['dimensions']
    )
}}

with products as (
    select * from {{ ref('int_products__performance_metrics') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,

        -- keys
        product_id,
        sku,

        -- attributes
        product_name,
        category,
        subcategory,
        brand,
        cost_price_gbp,
        rrp_gbp,
        is_active,
        is_age_restricted,

        -- performance metrics
        orders_containing_product,
        total_units_sold,
        total_revenue_gbp,
        total_discount_gbp,
        avg_selling_price_gbp,
        gross_margin_gbp,
        gross_margin_pct,
        times_substituted_away,

        -- inventory
        units_available,
        is_below_reorder_point,

        -- product tier
        case
            when total_revenue_gbp >= 10000 then 'hero'
            when total_revenue_gbp >= 1000 then 'core'
            when total_revenue_gbp > 0 then 'tail'
            else 'no_sales'
        end as product_tier,

        -- audit
        refreshed_at,
        current_timestamp() as dbt_updated_at

    from products
)

select * from final
