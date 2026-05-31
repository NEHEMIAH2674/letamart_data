{% docs surrogate_key %}
Surrogate primary key generated using dbt_utils.generate_surrogate_key.
A hashed combination of the natural key columns. Used as the unique_key
for incremental merge operations.
{% enddocs %}

{% docs customer_key %}
Surrogate key for the customer dimension.
Generated from customer_id using dbt_utils.generate_surrogate_key.
{% enddocs %}

{% docs product_key %}
Surrogate key for the product dimension.
Generated from product_id using dbt_utils.generate_surrogate_key.
{% enddocs %}

{% docs dbt_updated_at %}
Timestamp when this row was last written by a dbt run.
Used for audit and monitoring purposes.
{% enddocs %}

{% docs value_band %}
Customer value band derived from lifetime_value_gbp.
One of: high (>=£2000), mid (>=£500), low (>£0), none (no purchases).
{% enddocs %}

{% docs product_tier %}
Product performance tier derived from total_revenue_gbp.
One of: hero (>=£10000), core (>=£1000), tail (>£0), no_sales.
{% enddocs %}

{% docs stock_status %}
Current stock health classification for a product in a warehouse.
One of: out_of_stock (0 units available), critical (<=50% of reorder point),
low_stock (below reorder point), ok (above reorder point).
{% enddocs %}

{% docs gross_revenue_gbp %}
Total basket value of all delivered orders in GBP before discounts.
{% enddocs %}

{% docs net_revenue_gbp %}
Total revenue after all discounts have been deducted, in GBP.
Calculated as gross_revenue_gbp minus total_discount_gbp.
{% enddocs %}

{% docs avg_basket_value_gbp %}
Average basket value per order in GBP for the given time period.
{% enddocs %}

{% docs promo_attach_rate %}
Proportion of orders in the period that had a promotional code applied.
Expressed as a decimal between 0 and 1.
{% enddocs %}

{% docs revenue_wow_pct_change %}
Week-over-week percentage change in gross revenue.
Compares current day revenue to the same day 7 days prior.
Null when prior week data is not available.
{% enddocs %}

{% docs revenue_rolling_7d_gbp %}
Sum of gross revenue over the trailing 7 days including the current day.
Calculated using a window function partitioned by order_channel.
{% enddocs %}

{% docs cohort_month %}
The calendar month in which customers in this cohort first registered.
Truncated to the first day of the month for grouping purposes.
{% enddocs %}

{% docs pct_active_30d %}
Percentage of customers in the cohort who placed an order
in the last 30 days. Used as a retention health indicator.
{% enddocs %}

{% docs pct_active_90d %}
Percentage of customers in the cohort who placed an order
in the last 90 days. Used as a broader retention health indicator.
{% enddocs %}
