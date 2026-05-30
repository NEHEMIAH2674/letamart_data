{% docs stg_orders %}
Staged orders from the letamart raw layer. One row per customer order.
Casts and renames columns from the raw source. No business logic or joins.
Materialised as a view — always reflects the latest raw data.
{% enddocs %}

{% docs stg_order_items %}
Staged order line items from the letamart raw layer. One row per order line.
Includes derived columns: line_total_gbp and is_substituted flag.
Materialised as a view.
{% enddocs %}

{% docs stg_products %}
Staged product catalogue from the letamart raw layer. One row per product.
Cleans and standardises product name, category, subcategory and brand.
Materialised as a view.
{% enddocs %}

{% docs stg_customers %}
Staged customer master from the letamart raw layer. One row per registered customer.
Includes derived column: days_since_registration.
Materialised as a view.
{% enddocs %}

{% docs stg_inventory %}
Staged daily inventory snapshot from the letamart raw layer.
One row per product per warehouse per snapshot date.
Includes derived columns: units_available and is_below_reorder_point.
Materialised as a view.
{% enddocs %}

{% docs stg_promotions %}
Staged promotional campaigns from the letamart raw layer. One row per promotion.
Includes derived column: is_currently_valid.
Materialised as a view.
{% enddocs %}
