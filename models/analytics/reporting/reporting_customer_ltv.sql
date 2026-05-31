-- models/analytics/reporting/reporting_customer_ltv.sql
-- Monthly cohort LTV and retention rates.
-- Used for customer retention tracking.

{{
    config(
        materialized='table',
        tags=['reporting']
    )
}}

with customers as (
    select * from {{ ref('dim_customers') }}
    where has_ordered = true
),

cohort_summary as (
    select
        customer_segment,
        value_band,
        loyalty_tier,
        date_trunc(registration_date, month) as cohort_month,

        count(distinct customer_id) as customer_count,
        sum(lifetime_value_gbp) as cohort_ltv_gbp,
        avg(lifetime_value_gbp) as avg_ltv_gbp,
        avg(total_orders) as avg_orders_per_customer,
        avg(avg_order_value_gbp) as avg_basket_gbp,
        avg(days_since_last_order) as avg_days_since_last_order,
        countif(days_since_last_order <= 30) as active_last_30d,
        countif(days_since_last_order <= 90) as active_last_90d

    from customers
    group by 1, 2, 3, 4
)

select
    *,
    round(active_last_30d / nullif(customer_count, 0) * 100, 2) as pct_active_30d,
    round(active_last_90d / nullif(customer_count, 0) * 100, 2) as pct_active_90d

from cohort_summary
order by cohort_month desc, cohort_ltv_gbp desc
