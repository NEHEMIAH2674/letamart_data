-- models/analytics/dimensions/dim_date.sql
-- Date spine from project start date to 2 years ahead.
-- Full refresh on every run.

{{
    config(
        materialized='table',
        tags=['dimensions']
    )
}}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart='day',
        start_date="cast('" ~ var('letamart_start_date') ~ "' as date)",
        end_date="date_add(current_date(), interval 730 day)"
    ) }}
),

final as (
    select
        cast(date_day as date) as date_id,
        cast(date_day as date) as full_date,
        extract(year from date_day) as year,
        extract(month from date_day) as month,
        extract(day from date_day) as day_of_month,
        extract(week from date_day) as week_of_year,
        extract(dayofweek from date_day) as day_of_week,
        format_date('%A', date_day) as day_name,
        format_date('%B', date_day) as month_name,
        format_date('%Y-%m', date_day) as year_month,
        concat(
            'Q',
            cast(ceil(extract(month from date_day) / 3) as string),
            '-',
            cast(extract(year from date_day) as string)
        ) as quarter_label,
        extract(dayofweek from date_day) in (1, 7) as is_weekend,
        date_day = current_date() as is_today,
        date_day < current_date() as is_past,
        date_day <= date_trunc(current_date(), month) as is_month_to_date

    from date_spine
)

select * from final
