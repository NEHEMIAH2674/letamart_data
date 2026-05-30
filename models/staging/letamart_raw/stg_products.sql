-- models/staging/stg_products.sql
-- Staging layer: rename, cast, light cleaning only.
-- No business logic. No joins.

with source as (
    select * from {{ source('raw', 'products') }}
),

products as (
    select
        cast(product_id as string) as product_id,
        cast(sku as string) as sku,
        cast(cost_price_gbp as numeric) as cost_price_gbp,
        cast(rrp_gbp as numeric) as rrp_gbp,
        cast(weight_kg as numeric) as weight_kg,
        cast(is_alcohol as bool) as is_alcohol,
        cast(is_age_restricted as bool) as is_age_restricted,
        cast(is_active as bool) as is_active,
        trim(product_name) as product_name,
        lower(trim(category)) as category,
        lower(trim(subcategory)) as subcategory,
        lower(trim(brand)) as brand,

        -- audit
        current_timestamp() as refreshed_at

    from source
)

select * from products
