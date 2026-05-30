{% docs int_orders__basket_metrics %}
Intermediate model joining orders, order items and promotions.
One row per order with basket-level aggregates including total units,
basket value, discounts, substitution count and promotional details.
Ephemeral — no BigQuery table created, compiled inline by downstream models.
{% enddocs %}

{% docs int_customers__order_metrics %}
Intermediate model aggregating order history to customer grain.
Calculates lifetime value, average order value, order frequency,
recency metrics and RFM segmentation.
Ephemeral — no BigQuery table created, compiled inline by downstream models.
{% enddocs %}

{% docs int_products__performance_metrics %}
Intermediate model aggregating sales performance to product grain.
Calculates total revenue, gross margin, units sold, discount rate
and current inventory status.
Ephemeral — no BigQuery table created, compiled inline by downstream models.
{% enddocs %}
