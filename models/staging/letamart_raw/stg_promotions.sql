-- models/staging/stg_promotions.sql
-- Staging layer: rename, cast, light cleaning only.
-- No business logic. No joins.

with source as (
    select * from {{ source('raw', 'promotions') }}
),

promotions as (
    select
        cast(promo_id as string) as promo_id,
        cast(discount_value as numeric) as discount_value,
        cast(min_basket_gbp as numeric) as min_basket_gbp,
        cast(valid_from as date) as valid_from,
        cast(valid_to as date) as valid_to,
        cast(is_active as bool) as is_active,
        upper(trim(promo_code)) as promo_code,
        lower(trim(promo_type)) as promo_type,

        -- derived
        cast(valid_to as date) >= current_date()
        and cast(is_active as bool) = true as is_currently_valid,

        -- audit
        current_timestamp() as refreshed_at

    from source
)

select * from promotions
