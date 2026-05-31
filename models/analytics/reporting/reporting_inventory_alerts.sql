-- models/analytics/reporting/reporting_inventory_alerts.sql
-- Products at or below reorder point.
-- Drives daily Slack stock alerts.

{{
    config(
        materialized='table',
        tags=['reporting', 'alerts']
    )
}}

with inventory as (
    select * from {{ ref('stg_inventory') }} as inv
    where inv.snapshot_date = (
        select max(inv2.snapshot_date)
        from {{ ref('stg_inventory') }} as inv2
    )
),

products as (
    select
        product_id,
        product_name,
        category,
        brand,
        sku
    from {{ ref('dim_products') }}
),

alert_rows as (
    select
        i.product_id,
        p.product_name,
        p.sku,
        p.category,
        p.brand,
        i.warehouse_id,
        i.snapshot_date,
        i.units_on_hand,
        i.units_reserved,
        i.units_available,
        i.reorder_point,
        i.is_below_reorder_point,

        case
            when i.units_available = 0 then 'out_of_stock'
            when i.units_available <= (i.reorder_point * 0.5) then 'critical'
            when i.is_below_reorder_point then 'low_stock'
            else 'ok'
        end as stock_status,

        current_timestamp() as alert_generated_at

    from inventory as i
    inner join products as p on i.product_id = p.product_id
    where i.is_below_reorder_point = true
)

select * from alert_rows
order by stock_status, category, product_name
