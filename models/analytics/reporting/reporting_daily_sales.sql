-- models/analytics/reporting/reporting_daily_sales.sql
-- Pre-aggregated daily sales by channel.
-- Feeds dashboards and Slack alerts.

{{
    config(
        materialized='table',
        partition_by={
            'field': 'order_date',
            'data_type': 'date',
            'granularity': 'day'
        },
        tags=['reporting']
    )
}}

with orders as (
    select * from {{ ref('fact_orders') }}
    where is_delivered = true
),

daily as (
    select
        order_date,
        order_channel,
        count(distinct order_id) as total_orders,
        count(distinct customer_id) as unique_customers,
        sum(basket_value_gbp) as gross_revenue_gbp,
        sum(total_discount_gbp) as total_discount_gbp,
        sum(basket_value_gbp)
        - sum(total_discount_gbp) as net_revenue_gbp,
        avg(basket_value_gbp) as avg_basket_value_gbp,
        sum(total_units) as total_units_sold,
        countif(has_promo) as promo_orders,
        countif(has_promo) / count(*) as promo_attach_rate,
        sum(substituted_line_count) as total_substitutions

    from orders
    group by 1, 2
),

with_lag as (
    select
        *,
        lag(gross_revenue_gbp, 7) over (
            partition by order_channel
            order by order_date
        ) as revenue_7d_ago_gbp,

        sum(gross_revenue_gbp) over (
            partition by order_channel
            order by order_date
            rows between 6 preceding and current row
        ) as revenue_rolling_7d_gbp

    from daily
)

select
    *,
    case
        when revenue_7d_ago_gbp is null or revenue_7d_ago_gbp = 0 then null
        else round(
            (gross_revenue_gbp - revenue_7d_ago_gbp)
            / revenue_7d_ago_gbp * 100, 2
        )
    end as revenue_wow_pct_change

from with_lag
