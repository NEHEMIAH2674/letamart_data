-- models/staging/stg_customers.sql
-- Staging layer: rename, cast, light cleaning only.
-- No business logic. No joins.

with source as (
    select * from {{ source('raw', 'customers') }}
),

customers as (
    select
        cast(customer_id as string) as customer_id,
        cast(date_of_birth as date) as date_of_birth,
        cast(registered_at as timestamp) as registered_at,
        cast(is_active as bool) as is_active,
        cast(_loaded_at as timestamp) as refreshed_at,
        lower(trim(email)) as email,
        initcap(trim(first_name)) as first_name,
        initcap(trim(last_name)) as last_name,
        upper(trim(postcode)) as postcode,

        -- derived
        lower(trim(loyalty_tier)) as loyalty_tier,

        -- audit
        date_diff(
            current_date(),
            cast(registered_at as date),
            day
        ) as days_since_registration

    from source
)

select * from customers
