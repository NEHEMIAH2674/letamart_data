# letamart_dbt — Custom Macros

Reusable SQL macros for the letamart_dbt project.

## Macros

### `limit_data_in_dev(date_column, days=90)`
Limits data volume in the `dev` target to reduce BigQuery costs.
Applies a WHERE clause for the last N days in dev only — no filter in prod.

```sql
{{ limit_data_in_dev('order_created_at', 90) }}
```

---

### `generate_surrogate_key(field_list)`
Wrapper around `dbt_utils.generate_surrogate_key`.
Ensures consistent hashing across all models.

```sql
{{ generate_surrogate_key(['order_id', 'product_id']) }}
```

---

### `cents_to_pounds(column_name)`
Converts integer pence values to decimal GBP.

```sql
{{ cents_to_pounds('price_in_pence') }}
```

---

### `is_valid_email(column_name)`
Returns boolean true if the column matches a valid email format.

```sql
where not {{ is_valid_email('email') }}
```

---

### `get_revenue_metrics(gross_col, discount_col)`
Reusable revenue aggregation block.
Returns gross, net, avg revenue and discount rate.

```sql
{{ get_revenue_metrics('basket_value_gbp', 'total_discount_gbp') }}
```

---

### `safe_divide(numerator, denominator)`
Safe division returning null instead of error on divide by zero.

```sql
{{ safe_divide('total_revenue', 'total_orders') }}
```

---

### `current_timestamp_utc()`
Returns current timestamp in UTC for consistent timezone handling.

```sql
{{ current_timestamp_utc() }}
```
