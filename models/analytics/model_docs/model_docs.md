{% docs fact_orders %}
Fact table at order grain. One row per customer order.
Incremental merge strategy — processes only the last 3 days on each run.
Partitioned by order_date, clustered by order_status and order_channel.
Contains basket metrics, delivery flags and promotional details.
{% enddocs %}

{% docs fact_order_items %}
Fact table at order line grain. One row per product line within an order.
Incremental merge strategy — processes only the last 3 days on each run.
Partitioned by order_date, clustered by product_id and category.
Contains line-level revenue, discount and substitution details.
{% enddocs %}

{% docs dim_customers %}
Customer dimension table. One row per registered customer.
SCD Type 1 — full refresh on every daily run.
Contains lifetime value, RFM segmentation, order behaviour and value banding.
Clustered by loyalty_tier and customer_segment.
{% enddocs %}

{% docs dim_products %}
Product dimension table. One row per product in the catalogue.
SCD Type 1 — full refresh on every daily run.
Contains sales performance metrics, margin calculations and inventory status.
Clustered by category and subcategory.
{% enddocs %}

{% docs dim_date %}
Date dimension table. One row per calendar day.
Spans from project start date to 2 years ahead of current date.
Contains date attributes for time-based analysis and dashboard filtering.
{% enddocs %}

{% docs reporting_daily_sales %}
Pre-aggregated daily sales summary by channel.
Contains revenue, order count, basket value, discount rate and WoW % change.
Partitioned by order_date. Feeds dashboards and Slack daily alerts.
{% enddocs %}

{% docs reporting_inventory_alerts %}
Products currently at or below reorder point across all warehouses.
Stock status classified as: out_of_stock, critical, or low_stock.
Refreshed on every daily run. Feeds Slack inventory alerts.
{% enddocs %}

{% docs reporting_customer_ltv %}
Monthly cohort summary of customer lifetime value and retention rates.
Groups customers by cohort month, segment, value band and loyalty tier.
Used for retention tracking and cohort analysis in BI tools.
{% enddocs %}
