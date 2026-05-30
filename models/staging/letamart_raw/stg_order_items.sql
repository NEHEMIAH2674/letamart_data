-- models/staging/stg_order_items.sql
-- Staging layer: rename, cast, light cleaning only.
-- No business logic. No joins.

with source as (
    select * from {{ source('raw', 'order_items') }}
),

order_items as (
    select
        cast(order_item_id as string) as order_item_id,
        cast(order_id as string) as order_id,
        cast(product_id as string) as product_id,
        cast(substituted_product_id as string) as substituted_product_id,

        cast(quantity as int64) as quantity,
        cast(unit_price_gbp as numeric) as unit_price_gbp,
        cast(discount_amount_gbp as numeric) as discount_amount_gbp,

        -- derived
        cast(quantity as numeric) * cast(unit_price_gbp as numeric)
        - coalesce(cast(discount_amount_gbp as numeric), 0)
            as line_total_gbp,

        substituted_product_id is not null as is_substituted,

        -- audit
        current_timestamp() as refreshed_at

    from source
)

select * from order_items
