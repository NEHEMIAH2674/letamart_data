-- models/staging/stg_orders.sql
-- Staging layer: rename, cast, light cleaning only.
-- No business logic. No joins.

with source as (
    select * from {{ source('raw', 'orders') }}
),

orders as (
    select
        -- keys
        cast(order_id as string) as order_id,
        cast(customer_id as string) as customer_id,
        cast(delivery_address_id as string) as delivery_address_id,
        cast(promo_code as string) as promo_code,

        -- descriptors
        cast(created_at as timestamp) as order_created_at,
        cast(delivery_slot_start as timestamp) as delivery_slot_start_at,

        -- timestamps
        cast(delivery_slot_end as timestamp) as delivery_slot_end_at,
        cast(_loaded_at as timestamp) as refreshed_at,
        lower(trim(status)) as order_status,

        -- audit
        lower(trim(channel)) as order_channel

    from source
)

select * from orders
