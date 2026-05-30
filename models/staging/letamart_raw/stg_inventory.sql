-- models/staging/stg_inventory.sql
-- Staging layer: rename, cast, light cleaning only.
-- No business logic. No joins.

with source as (
    select * from {{ source('raw', 'inventory') }}
),

inventory as (
    select
        cast(inventory_id as string) as inventory_id,
        cast(product_id as string) as product_id,
        cast(warehouse_id as string) as warehouse_id,
        cast(snapshot_date as date) as snapshot_date,
        cast(units_on_hand as int64) as units_on_hand,
        cast(units_reserved as int64) as units_reserved,
        cast(units_in_transit as int64) as units_in_transit,
        cast(reorder_point as int64) as reorder_point,

        -- derived
        cast(_loaded_at as timestamp) as refreshed_at,

        cast(units_on_hand as int64)
        - cast(units_reserved as int64) as units_available,

        -- audit
        cast(units_on_hand as int64)
        <= cast(reorder_point as int64) as is_below_reorder_point

    from source
)

select * from inventory
