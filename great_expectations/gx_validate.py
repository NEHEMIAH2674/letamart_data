"""
great_expectations/gx_validate.py
-----------------------------------
Runs Great Expectations validations against letamart BigQuery tables.
Uses GX 1.18 Fluent API with ephemeral context.

Usage:
    python great_expectations/gx_validate.py

.env requirements:
    GCP_PROJECT_ID=npd-01
    GCP_LOCATION=EU
"""

import os
import sys
from dotenv import load_dotenv
import great_expectations as gx
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET    = "letamart_dev_staging"

bq_client  = bigquery.Client(project=PROJECT_ID)


def get_df(table: str):
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.{table}`"
    print(f"   Fetching {PROJECT_ID}.{DATASET}.{table}...")
    return bq_client.query(query).to_dataframe()


def validate_table(context, name: str, df, expectations: list) -> dict:
    """Run a list of expectations against a dataframe."""
    print(f"\n📋 Validating {name}...")

    # Add pandas datasource
    datasource = context.data_sources.add_pandas(name=f"{name}_source")
    asset      = datasource.add_dataframe_asset(name=name)
    batch_def  = asset.add_batch_definition_whole_dataframe(f"{name}_batch")
    batch      = batch_def.get_batch(batch_parameters={"dataframe": df})

    # Create suite and add expectations
    suite = context.suites.add(gx.ExpectationSuite(name=f"{name}_suite"))
    for expectation in expectations:
        suite.add_expectation(expectation)

    # Run validation
    definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name=f"{name}_validation",
            data=batch_def,
            suite=suite,
        )
    )

    result = definition.run(batch_parameters={"dataframe": df})

    # Summarise
    stats   = result.statistics
    passed  = stats["successful_expectations"]
    total   = stats["evaluated_expectations"]
    failed  = stats["unsuccessful_expectations"]
    success = result.success

    icon = "✅" if success else "🚨"
    print(f"{icon} {name}: {passed}/{total} passed"
          + (f" — {failed} FAILED" if failed else ""))

    if not success:
        for r in result.results:
            if not r.success:
                print(f"   ❌ {r.expectation_config.type} — "
                      f"{r.expectation_config.kwargs}")

    return {"name": name, "success": success, "passed": passed, "total": total}


def run_validations():
    print("\n🔍 letamart — Great Expectations validation")
    print(f"   Project: {PROJECT_ID} | Dataset: {DATASET}")
    print("=" * 55)

    context = gx.get_context(mode="ephemeral")
    results = []

    # ── stg_orders ────────────────────────────────────
    df_orders = get_df("stg_orders")
    results.append(validate_table(
        context, "stg_orders", df_orders,
        [
            gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id"),
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="order_status",
                value_set=["pending", "confirmed", "picking",
                           "dispatched", "delivered", "cancelled", "returned"]
            ),
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="order_channel",
                value_set=["web", "app", "partner"]
            ),
            gx.expectations.ExpectTableRowCountToBeBetween(min_value=100),
        ]
    ))

    # ── stg_order_items ───────────────────────────────
    df_items = get_df("stg_order_items")
    results.append(validate_table(
        context, "stg_order_items", df_items,
        [
            gx.expectations.ExpectColumnValuesToNotBeNull(column="order_item_id"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="order_item_id"),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="product_id"),
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="quantity", min_value=1, max_value=99
            ),
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="unit_price_gbp", min_value=0.01
            ),
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="line_total_gbp", min_value=0.01
            ),
            gx.expectations.ExpectTableRowCountToBeBetween(min_value=500),
        ]
    ))

    # ── stg_customers ─────────────────────────────────
    df_customers = get_df("stg_customers")
    results.append(validate_table(
        context, "stg_customers", df_customers,
        [
            gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="customer_id"),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="email"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="email"),
            gx.expectations.ExpectColumnValuesToMatchRegex(
                column="email",
                regex=r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
            ),
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="loyalty_tier",
                value_set=["bronze", "silver", "gold", "platinum"]
            ),
            gx.expectations.ExpectColumnValuesToBeBetween(
            column="days_since_registration", min_value=-365, max_value=3000
       ),

        ]
    ))

    # ── stg_products ──────────────────────────────────
    df_products = get_df("stg_products")
    results.append(validate_table(
        context, "stg_products", df_products,
        [
            gx.expectations.ExpectColumnValuesToNotBeNull(column="product_id"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="product_id"),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="sku"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="sku"),
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="cost_price_gbp", min_value=0.01
            ),
            gx.expectations.ExpectColumnValuesToBeBetween(
                column="rrp_gbp", min_value=0.01
            ),
            gx.expectations.ExpectTableRowCountToBeBetween(
                min_value=50, max_value=500
            ),
        ]
    ))

    # ── Final summary ─────────────────────────────────
    print("\n" + "=" * 55)
    print("📊 Final summary")
    print("=" * 55)

    overall = True
    for r in results:
        icon = "✅" if r["success"] else "🚨"
        print(f"{icon} {r['name']}: {r['passed']}/{r['total']} passed")
        if not r["success"]:
            overall = False

    print()
    if overall:
        print("✅ All GX validations passed")
    else:
        print("🚨 Some validations failed")
        sys.exit(1)


if __name__ == "__main__":
    run_validations()
