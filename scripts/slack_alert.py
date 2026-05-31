"""
scripts/slack_alert.py
-----------------------
Reads dbt run results and sends formatted Slack alerts.
Called by GitHub Actions after every dbt run.

Usage:
    python scripts/slack_alert.py --run-type hourly
    python scripts/slack_alert.py --run-type daily
    python scripts/slack_alert.py --run-type daily --alert-type inventory

Env vars required:
    SLACK_WEBHOOK_URL   - Incoming webhook URL from your Slack app
    GCP_PROJECT_ID      - BigQuery project ID
    GCP_DATASET_ID      - BigQuery dataset ID
    GCP_LOCATION        - BigQuery location
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import urllib.error

# ── Paths ─────────────────────────────────────────────────────
RUN_RESULTS_PATH = Path("target/run_results.json")

# ── Config ────────────────────────────────────────────────────
WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
PROJECT_ID  = os.getenv("GCP_PROJECT_ID", "npd-01")
DATASET_ID  = os.getenv("GCP_DATASET_ID", "letamart_raw")


# ── Helpers ───────────────────────────────────────────────────
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def send_to_slack(payload: dict):
    if not WEBHOOK_URL:
        print("⚠️  SLACK_WEBHOOK_URL not set — skipping alert")
        return

    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"📨 Slack alert sent — status: {resp.status}")
    except urllib.error.URLError as e:
        print(f"⚠️  Slack alert failed: {e}", file=sys.stderr)


def load_run_results() -> dict:
    if not RUN_RESULTS_PATH.exists():
        print(f"⚠️  {RUN_RESULTS_PATH} not found — did the dbt run complete?")
        return {}
    with open(RUN_RESULTS_PATH) as f:
        return json.load(f)


def summarise_run(run_results: dict) -> dict:
    results  = run_results.get("results", [])
    elapsed  = run_results.get("elapsed_time", 0)

    success  = [r for r in results if r["status"] in ("success", "pass")]
    warnings = [r for r in results if r["status"] == "warn"]
    errors   = [r for r in results if r["status"] in ("error", "fail")]
    skipped  = [r for r in results if r["status"] == "skipped"]

    return {
        "total":       len(results),
        "success":     len(success),
        "warnings":    len(warnings),
        "errors":      len(errors),
        "skipped":     len(skipped),
        "elapsed":     round(elapsed, 1),
        "error_nodes": [r["unique_id"].split(".")[-1] for r in errors],
        "warn_nodes":  [r["unique_id"].split(".")[-1] for r in warnings],
    }


# ── Alert builders ────────────────────────────────────────────
def build_run_summary_payload(summary: dict, run_type: str) -> dict:
    passed  = summary["errors"] == 0
    status  = "✅ Passed" if passed else "🚨 Failed"
    colour  = "#2eb886" if passed else "#e01e5a"
    emoji   = "✅" if passed else "🚨"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} letamart_dbt — {run_type} run {status}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Models run:*\n{summary['total']}"},
                {"type": "mrkdwn", "text": f"*Passed:*\n{summary['success']}"},
                {"type": "mrkdwn", "text": f"*Errors:*\n{summary['errors']}"},
                {"type": "mrkdwn", "text": f"*Warnings:*\n{summary['warnings']}"},
                {"type": "mrkdwn", "text": f"*Elapsed:*\n{summary['elapsed']}s"},
                {"type": "mrkdwn", "text": f"*Time:*\n{now_utc()}"},
            ]
        }
    ]

    if summary["error_nodes"]:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Failed models:*\n"
                    f"```{chr(10).join(summary['error_nodes'])}```"
                )
            }
        })

    if summary["warn_nodes"]:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Warnings:*\n"
                    f"```{chr(10).join(summary['warn_nodes'])}```"
                )
            }
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Project: `{PROJECT_ID}` | Dataset: `{DATASET_ID}`"
            }
        ]
    })

    return {
        "attachments": [
            {
                "color":  colour,
                "blocks": blocks
            }
        ]
    }


def build_inventory_alert_payload() -> dict:
    """
    Queries BigQuery reporting_inventory_alerts table and builds Slack payload.
    Falls back to a simple message if BigQuery is unavailable.
    """
    try:
        from google.cloud import bigquery

        client  = bigquery.Client(project=PROJECT_ID)
        dataset = DATASET_ID.replace("raw", "prod_analytics")

        query = f"""
            select
                stock_status,
                product_name,
                category,
                warehouse_id,
                units_available,
                reorder_point
            from `{PROJECT_ID}.{dataset}.reporting_inventory_alerts`
            order by
                case stock_status
                    when 'out_of_stock' then 1
                    when 'critical'     then 2
                    when 'low_stock'    then 3
                end,
                category,
                product_name
            limit 20
        """

        rows = list(client.query(query).result())

        if not rows:
            return {
                "text": "📦 *letamart inventory check* — all products above reorder point ✅"
            }

        out_of_stock = [r for r in rows if r["stock_status"] == "out_of_stock"]
        critical     = [r for r in rows if r["stock_status"] == "critical"]
        low_stock    = [r for r in rows if r["stock_status"] == "low_stock"]

        lines = [f"*📦 Inventory Alert — {now_utc()}*\n"]

        for item in out_of_stock[:5]:
            lines.append(
                f"🔴 *{item['product_name']}* — OUT OF STOCK "
                f"({item['category']} | {item['warehouse_id']})"
            )

        for item in critical[:5]:
            lines.append(
                f"🟠 *{item['product_name']}* — CRITICAL "
                f"({item['units_available']} units | reorder at {item['reorder_point']})"
            )

        for item in low_stock[:5]:
            lines.append(
                f"🟡 *{item['product_name']}* — low stock "
                f"({item['units_available']} units)"
            )

        total = len(rows)
        if total > 15:
            lines.append(f"\n_...and {total - 15} more. Check BigQuery for full list._")

        return {
            "attachments": [
                {
                    "color": "#e01e5a",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "\n".join(lines)
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": (
                                        f"Project: `{PROJECT_ID}` | "
                                        f"Table: `reporting_inventory_alerts`"
                                    )
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    except Exception as e:
        print(f"⚠️  Could not query inventory alerts: {e}")
        return {
            "text": f"📦 *letamart inventory alert* — could not query BigQuery: {e}"
        }


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Send letamart dbt Slack alerts")
    parser.add_argument(
        "--run-type",
        default="scheduled",
        choices=["hourly", "daily", "scheduled", "manual"],
        help="Type of dbt run"
    )
    parser.add_argument(
        "--alert-type",
        default="run_results",
        choices=["run_results", "inventory"],
        help="Type of alert to send"
    )
    args = parser.parse_args()

    print(f"🔔 Sending {args.alert_type} alert for {args.run_type} run...")

    if args.alert_type == "inventory":
        payload = build_inventory_alert_payload()
        send_to_slack(payload)

    else:
        run_results = load_run_results()
        if not run_results:
            print("No run results found — skipping alert")
            sys.exit(0)

        summary = summarise_run(run_results)
        payload = build_run_summary_payload(summary, args.run_type)
        send_to_slack(payload)

        print(
            f"Summary: {summary['success']}/{summary['total']} passed, "
            f"{summary['errors']} errors, {summary['elapsed']}s elapsed"
        )

        if summary["errors"] > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
