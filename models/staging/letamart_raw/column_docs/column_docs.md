{% docs order_id %}
Unique identifier for each customer order. Primary key of the orders table.
{% enddocs %}

{% docs customer_id %}
Unique identifier for each registered customer. Foreign key to the customers table.
{% enddocs %}

{% docs product_id %}
Unique identifier for each product in the catalogue. Foreign key to the products table.
{% enddocs %}

{% docs order_status %}
Current status of the order. One of: pending, confirmed, picking, dispatched, delivered, cancelled, returned.
{% enddocs %}

{% docs order_channel %}
Channel through which the order was placed. One of: web, app, partner.
{% enddocs %}

{% docs loyalty_tier %}
Customer loyalty tier based on lifetime value and order frequency. One of: bronze, silver, gold, platinum.
{% enddocs %}

{% docs promo_code %}
Promotional code applied to the order. Null if no promotion was used.
{% enddocs %}

{% docs refreshed_at %}
Timestamp when this record was last loaded into the raw layer. Used for data freshness monitoring.
{% enddocs %}

{% docs is_active %}
Boolean flag indicating whether this record is currently active.
{% enddocs %}

{% docs is_substituted %}
Boolean flag indicating whether the ordered product was substituted with an alternative item.
{% enddocs %}

{% docs line_total_gbp %}
Total value of the order line in GBP after discounts. Calculated as (quantity × unit_price) - discount_amount.
{% enddocs %}

{% docs units_available %}
Number of units currently available for sale. Calculated as units_on_hand minus units_reserved.
{% enddocs %}

{% docs is_below_reorder_point %}
Boolean flag indicating whether current stock is at or below the reorder threshold.
{% enddocs %}

{% docs is_currently_valid %}
Boolean flag indicating whether the promotion is currently active and within its valid date range.
{% enddocs %}
