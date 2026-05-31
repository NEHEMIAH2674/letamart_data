# letamart_dbt

> **An end-to-end analytics engineering portfolio project** built on dbt + BigQuery, modelling an online supermarket from raw transactional data through to BI-ready facts, dimensions and reporting tables — with automated testing, documentation, Slack alerts and scheduled GitHub Actions pipelines.

**Author:** Nehemiah Onyinge
**Stack:** dbt 1.11 · BigQuery · Python · GitHub Actions · Slack
**Repo:** https://github.com/NEHEMIAH2674/letamart_data

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Strategy Flowchart](#2-strategy-flowchart)
3. [Solution Architecture](#3-solution-architecture)
4. [Project Structure](#4-project-structure)
5. [Setup Guide](#5-setup-guide)
6. [Data Generation](#6-data-generation)
7. [dbt Layers](#7-dbt-layers)
8. [Custom Macros](#8-custom-macros)
9. [Testing Strategy](#9-testing-strategy)
10. [Documentation](#10-documentation)
11. [BigQuery — Live Datasets](#11-bigquery--live-datasets)
12. [Scheduling & Orchestration](#12-scheduling--orchestration)
13. [Slack Alerts](#13-slack-alerts)
14. [Key Design Decisions](#14-key-design-decisions)

---

## 1. Problem Statement

An online supermarket generates transactional data across orders, products, customers, inventory and promotions. This data lands in BigQuery as raw tables with inconsistent types, no business logic and no documentation.

**The challenge:**
- Raw data has no consistent naming or typing conventions
- Business analysts can't answer questions like "What is our customer LTV by cohort?" or "Which products are below reorder point?" without complex ad-hoc SQL
- There is no data quality monitoring — bad data goes undetected
- There is no scheduled pipeline — everything is manual

**The solution:**
A fully automated dbt pipeline that transforms raw data into clean, tested, documented and BI-ready tables — with Slack alerts, hourly incremental updates and daily full refreshes scheduled via GitHub Actions.

---

## 2. Strategy Flowchart

```mermaid
flowchart TD
    A([🏪 Business Problem\nRaw data · no logic · no quality · no schedule]):::problem

    subgraph INGEST["📥 Ingest"]
        B[generate_raw_data.py\nRuns daily at 12:00 UTC]:::script
        C[(BigQuery\nletamart_raw\n6 tables · ~23k rows)]:::bq
    end

    subgraph TRANSFORM["⚙️ Transform — dbt pipeline"]
        D[Staging\nstg_* · cast & rename · views\n6 models · 58 tests]:::staging
        E[Intermediate\nint_* · joins & metrics · ephemeral\n3 models · 9 tests]:::intermediate
        subgraph ANALYTICS["Analytics layer"]
            F[Facts\nfact_orders · fact_order_items\nincremental · partitioned]:::facts
            G[Dimensions\ndim_customers · dim_products · dim_date\nSCD Type 1]:::dims
            H[Reporting\nreporting_daily_sales\nreporting_inventory_alerts · reporting_customer_ltv]:::reporting
        end
    end

    subgraph VALIDATE["✅ Validate"]
        I[dbt test\n127 tests passing\nunique · not_null · relationships]:::test
    end

    subgraph SCHEDULE["⏰ Schedule — GitHub Actions"]
        J[Hourly run\ndbt_hourly.yml · incremental facts]:::hourly
        K[Daily full run\ndbt_daily.yml · 12:00 UTC]:::daily
        L[CI on every PR\ndbt_ci.yml · compile + tests]:::ci
    end

    subgraph ALERT["🔔 Alerts"]
        M[Slack\nRun summary · Inventory alerts · Failure pings]:::slack
    end

    subgraph CONSUME["📊 Consume"]
        N[Looker Studio\nCEO · Commercial · Operations]:::bi
        O[dbt docs\nLineage graph · Column docs]:::docs
    end

    P([✅ Business Outcome\nTrusted data · fast decisions · zero manual SQL]):::outcome

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F & G & H
    F & G & H --> I
    I --> J & K & L
    J & K --> M
    K --> N & O
    M --> N
    N & O --> P

    classDef problem      fill:#F1EFE8,stroke:#B4B2A9,color:#2C2C2A
    classDef script       fill:#E1F5EE,stroke:#5DCAA5,color:#04342C
    classDef bq           fill:#E6F1FB,stroke:#85B7EB,color:#042C53
    classDef staging      fill:#E1F5EE,stroke:#5DCAA5,color:#04342C
    classDef intermediate fill:#EEEDFE,stroke:#AFA9EC,color:#26215C
    classDef facts        fill:#FAECE7,stroke:#F0997B,color:#4A1B0C
    classDef dims         fill:#FAECE7,stroke:#F0997B,color:#4A1B0C
    classDef reporting    fill:#FAECE7,stroke:#F0997B,color:#4A1B0C
    classDef test         fill:#E6F1FB,stroke:#85B7EB,color:#042C53
    classDef hourly       fill:#FAEEDA,stroke:#FAC775,color:#412402
    classDef daily        fill:#FAEEDA,stroke:#FAC775,color:#412402
    classDef ci           fill:#FAEEDA,stroke:#FAC775,color:#412402
    classDef slack        fill:#F1EFE8,stroke:#B4B2A9,color:#2C2C2A
    classDef bi           fill:#E1F5EE,stroke:#5DCAA5,color:#04342C
    classDef docs         fill:#E1F5EE,stroke:#5DCAA5,color:#04342C
    classDef outcome      fill:#E1F5EE,stroke:#1D9E75,color:#04342C
```

---

## 3. Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                    │
│                                                                      │
│  Python script          dbt pipeline             BI / Alerts        │
│  (daily 12:00)                                                       │
│                                                                      │
│  generate_raw_data.py                                                │
│       │                                                              │
│       ▼                                                              │
│  BigQuery                                                            │
│  letamart_raw          ┌──────────┐                                  │
│  ┌──────────┐          │ staging  │  views                           │
│  │ orders   │ ────────▶│ stg_*    │                                  │
│  │ items    │          └────┬─────┘                                  │
│  │ products │               │                                        │
│  │ customers│          ┌────▼──────────┐                             │
│  │ inventory│          │ intermediate  │  ephemeral                  │
│  │ promos   │          │ int_*         │                             │
│  └──────────┘          └────┬──────────┘                            │
│                              │                                       │
│                    ┌─────────▼──────────────────┐                   │
│                    │      analytics              │                   │
│                    │  facts/    (incremental)    │                   │
│                    │  dimensions/ (full refresh) │                   │
│                    │  reporting/  (full refresh) │                   │
│                    └─────────┬──────────────────┘                   │
│                              │                                       │
│                    ┌─────────▼──────────────────┐                   │
│                    │   Looker Studio / BI        │                   │
│                    │   Slack inventory alerts    │                   │
│                    └────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

### dbt Lineage Graph

> Run `dbt docs generate && dbt docs serve` to view the interactive lineage graph at http://localhost:8080

![dbt lineage graph](docs/lineage_graph.png)

### Layer Responsibilities

| Layer | Materialisation | Responsibility |
|---|---|---|
| `staging` | view | Rename, cast, light cleaning. One model per source table. No joins, no business logic. |
| `intermediate` | ephemeral | Business logic, joins, derived metrics. No storage cost — compiled inline. |
| `analytics/facts` | incremental (merge) | Order and line-item facts. Partitioned by `order_date`, clustered for query efficiency. |
| `analytics/dimensions` | table | Customer 360, product catalogue, date spine. SCD Type 1. |
| `analytics/reporting` | table | Pre-aggregated summaries for dashboards and Slack alerts. |

---

## 4. Project Structure

```
letamart_dbt/
├── models/
│   ├── staging/
│   │   └── letamart_raw/
│   │       ├── column_docs/       # reusable column descriptions
│   │       ├── model_docs/        # model descriptions
│   │       ├── src_letamart.yml   # source definitions + freshness + tests
│   │       ├── stg_models.yml     # staging model tests + doc references
│   │       ├── stg_orders.sql
│   │       ├── stg_order_items.sql
│   │       ├── stg_products.sql
│   │       ├── stg_customers.sql
│   │       ├── stg_inventory.sql
│   │       └── stg_promotions.sql
│   ├── intermediate/
│   │   ├── column_docs/
│   │   ├── model_docs/
│   │   ├── int_models.yml
│   │   ├── int_orders__basket_metrics.sql
│   │   ├── int_customers__order_metrics.sql
│   │   └── int_products__performance_metrics.sql
│   └── analytics/
│       ├── column_docs/
│       ├── model_docs/
│       ├── analytics_models.yml
│       ├── facts/
│       │   ├── fact_orders.sql
│       │   └── fact_order_items.sql
│       ├── dimensions/
│       │   ├── dim_customers.sql
│       │   ├── dim_products.sql
│       │   └── dim_date.sql
│       └── reporting/
│           ├── reporting_daily_sales.sql
│           ├── reporting_inventory_alerts.sql
│           └── reporting_customer_ltv.sql
├── macros/
│   ├── README.md
│   ├── limit_data_in_dev.sql
│   ├── generate_surrogate_key.sql
│   ├── cents_to_pounds.sql
│   ├── is_valid_email.sql
│   ├── get_revenue_metrics.sql
│   ├── safe_divide.sql
│   └── current_timestamp_utc.sql
├── scripts/
│   ├── generate_raw_data.py       # generates realistic supermarket data → BigQuery
│   └── slack_alert.py             # sends run results + inventory alerts to Slack
├── .github/workflows/
│   ├── dbt_ci.yml                 # PR check: compile + source tests
│   ├── dbt_hourly.yml             # hourly incremental fact refresh
│   └── dbt_daily.yml              # daily full run + docs + Slack alerts
├── .sqlfluff                      # SQL linting rules
├── .pre-commit-config.yaml        # pre-commit hooks (SQLFluff + file checks)
├── dbt_project.yml                # dbt project configuration
├── packages.yml                   # dbt packages (dbt_utils)
├── profiles.yml                   # BigQuery connection profiles
└── requirements.txt               # Python dependencies
```

---

## 5. Setup Guide

### 5.1 Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Git + GitHub account
- A personal GCP project with BigQuery enabled
- A Slack workspace with incoming webhooks enabled

### 5.2 GCP Configuration

This project uses a **separate gcloud configuration** to isolate the personal GCP account from any existing org accounts on the same machine.

```bash
# Check which account is currently active
gcloud config get-value account

# Create a new isolated configuration for this project
gcloud config configurations create letamart

# Log in with your personal Google account
gcloud auth login

# Point the configuration at your GCP project
gcloud config set project YOUR_PROJECT_ID

# Set up Application Default Credentials (used by dbt to authenticate)
gcloud auth application-default login

# Enable required APIs
gcloud services enable bigquery.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable iamcredentials.googleapis.com --project=YOUR_PROJECT_ID

# Confirm your configuration
gcloud config configurations list
```

**Expected output:**
```
NAME       IS_ACTIVE  ACCOUNT                    PROJECT
letamart   True       your@gmail.com             your-project-id
work       False      work@organization.com      org-project-id
```

> **Why a separate configuration?** Running `gcloud config configurations activate work` switches back to your org account instantly. The two projects never interfere with each other.

### 5.3 Python Environment

```bash
# Clone the repo
git clone https://github.com/NEHEMIAH2674/letamart_data.git
cd letamart_data

# Create virtual environment at the parent level
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate      # macOS/Linux

# Install all dependencies
cd letamart_dbt
pip install -r requirements.txt
```

### 5.4 dbt Setup

```bash
# Install dbt packages (dbt_utils)
dbt deps

# Validate the connection
dbt debug
```

**Expected output:**
```
profiles.yml file [OK found and valid]
dbt_project.yml file [OK found and valid]
Connection test: [OK connection ok]
All checks passed!
```

### 5.5 BigQuery Connection

The `profiles.yml` in the repo root contains two targets:

```yaml
letamart_dbt:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth          # uses gcloud ADC — no key files
      project: npd-01
      dataset: letamart_dev
      location: EU
      threads: 4
    prod:
      type: bigquery
      method: oauth
      project: npd-01
      dataset: letamart_prod
      location: EU
      threads: 8
```

> **Security note:** `method: oauth` uses Application Default Credentials — no service account key files are stored in the repo. GitHub Actions uses Workload Identity Federation for keyless authentication.

---

## 6. Data Generation

The project includes a Python script that generates realistic supermarket data and loads it into BigQuery. This makes the project fully self-contained — no external data sources required.

```bash
# Set environment variables (create a .env file — never committed)
GCP_PROJECT_ID=your-project-id
GCP_DATASET_ID=letamart_raw
GCP_LOCATION=EU
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Run the generator
python scripts/generate_raw_data.py
```

**Generated tables:**

| Table | Rows | Description |
|---|---|---|
| `products` | 100 | Product catalogue across 10 categories |
| `customers` | 500 | Registered customers with loyalty tiers |
| `promotions` | 20 | Discount campaigns |
| `orders` | 3,000 | Customer orders with status and channel |
| `order_items` | ~19,000 | Line items per order |
| `inventory` | 400 | Daily stock snapshots across 4 warehouses |

The script sends a Slack alert on completion with row counts and elapsed time.

---

## 7. dbt Layers

### 7.1 Sources

Defined in `models/staging/letamart_raw/src_letamart.yml`. Sources tell dbt where to find raw data in BigQuery and define database and schema (`npd-01.letamart_raw`), data freshness thresholds (warn after 25h, error after 48h), and column-level tests on the raw tables.

### 7.2 Staging

**Materialisation:** view | **Models:** 6 | **Tests:** 58

Staging models are the first transformation layer. They follow strict rules — one model per source table, cast all columns to correct types, rename to consistent conventions, add light derived columns (e.g. `line_total_gbp`, `is_substituted`), add `refreshed_at` audit column. No joins, no business logic.

```sql
-- Example: stg_orders.sql
with source as (
    select * from {{ source('raw', 'orders') }}
),

orders as (
    select
        cast(order_id    as string)    as order_id,
        cast(customer_id as string)    as customer_id,
        lower(trim(status))            as order_status,
        lower(trim(channel))           as order_channel,
        cast(created_at  as timestamp) as order_created_at,
        cast(_loaded_at  as timestamp) as refreshed_at
    from source
)

select * from orders
```

### 7.3 Intermediate

**Materialisation:** ephemeral | **Models:** 3 | **Tests:** 9

Intermediate models contain all business logic. They are ephemeral — no BigQuery tables are created. SQL is compiled inline by downstream models, saving storage cost.

| Model | What it does |
|---|---|
| `int_orders__basket_metrics` | Joins orders + items + promotions. Calculates basket value, discount, substitution count. |
| `int_customers__order_metrics` | Aggregates to customer grain. LTV, average order value, RFM segmentation. |
| `int_products__performance_metrics` | Aggregates to product grain. Revenue, margin, units sold, inventory status. |

**Naming convention:** `int_{entity}__{transformation}` — double underscore separates entity from transformation verb.

### 7.4 Analytics — Facts

**Materialisation:** incremental (merge) | **Partition:** `order_date` | **Cluster:** `order_status`, `order_channel`

Fact tables use an incremental merge strategy — only the last 3 days are processed on each run, dramatically reducing BigQuery compute costs.

```sql
{% if is_incremental() %}
    where order_date >= date_sub(current_date(), interval 3 day)
{% endif %}
```

| Model | Rows | Grain |
|---|---|---|
| `fact_orders` | ~3,000 | One row per order |
| `fact_order_items` | ~19,000 | One row per order line |

### 7.5 Analytics — Dimensions

**Materialisation:** table (SCD Type 1 — full refresh daily)

| Model | Rows | Description |
|---|---|---|
| `dim_customers` | 500 | Customer 360 with LTV, RFM segment (`active`, `at_risk`, `lapsing`, `churned`) and value band (`high`, `mid`, `low`) |
| `dim_products` | 100 | Product catalogue with gross margin %, performance tier (`hero`, `core`, `tail`) and inventory status |
| `dim_date` | 2,000+ | Date spine from 2023 to 2 years ahead with week/month/quarter labels |

### 7.6 Analytics — Reporting

**Materialisation:** table (full refresh daily)

| Model | Description |
|---|---|
| `reporting_daily_sales` | Daily revenue by channel with WoW % change and 7-day rolling revenue |
| `reporting_inventory_alerts` | Products below reorder point classified as `out_of_stock`, `critical` or `low_stock` |
| `reporting_customer_ltv` | Monthly cohort LTV, retention rates (`pct_active_30d`, `pct_active_90d`) |

---

## 8. Custom Macros

Located in `macros/`. See `macros/README.md` for full documentation.

| Macro | Usage | Purpose |
|---|---|---|
| `limit_data_in_dev(date_col, days)` | `{{ limit_data_in_dev('order_created_at', 90) }}` | Adds WHERE clause in dev only — reduces cost |
| `generate_surrogate_key(fields)` | `{{ generate_surrogate_key(['order_id']) }}` | Consistent surrogate key hashing |
| `cents_to_pounds(col)` | `{{ cents_to_pounds('price_pence') }}` | Integer pence → decimal GBP |
| `is_valid_email(col)` | `{{ is_valid_email('email') }}` | Regex email validation |
| `get_revenue_metrics(gross, discount)` | `{{ get_revenue_metrics('basket_value_gbp', 'discount_gbp') }}` | Reusable revenue aggregation |
| `safe_divide(num, denom)` | `{{ safe_divide('revenue', 'orders') }}` | Null-safe division |
| `current_timestamp_utc()` | `{{ current_timestamp_utc() }}` | Consistent UTC timestamps |

---

## 9. Testing Strategy

Tests are defined in YAML files alongside each model. dbt runs them with `dbt test`.

**Test types used:**
- `unique` — no duplicate primary keys
- `not_null` — required columns are always populated
- `accepted_values` — categorical columns only contain expected values
- `relationships` — foreign keys reference valid records in parent tables

**Test counts by layer:**

| Layer | Models | Tests |
|---|---|---|
| Sources (raw) | 6 | 30 |
| Staging | 6 | 58 |
| Intermediate | 3 | 9 |
| Analytics | 8 | 30 |
| **Total** | **23** | **127** |

```bash
dbt test                          # run all tests
dbt test --select staging         # staging only
dbt test --select intermediate    # intermediate only
dbt test --select analytics       # analytics only
```

---

## 10. Documentation

dbt generates an interactive documentation site from the descriptions and tests defined in YAML files.

```bash
dbt docs generate    # generate the catalog
dbt docs serve       # serve locally at http://localhost:8080
```

Every model, column and source in this project has a written description. Column descriptions are defined once in `column_docs/` markdown files and referenced across multiple models using `{{ doc('column_name') }}`.

---

## 11. BigQuery — Live Datasets

All datasets live in GCP project `npd-01`. The pipeline creates and maintains 4 datasets automatically.

### Raw layer — `letamart_raw`
> 6 source tables generated daily by `generate_raw_data.py`

![letamart_raw dataset](docs/bigquery_raw.png)

### Staging layer — `letamart_prod_staging`
> 6 views materialised by dbt — light cleaning and casting only

![letamart_prod_staging dataset](docs/bigquery_prod_staging.png)

### Analytics layer — `letamart_prod_analytics`
> 8 tables materialised by dbt — facts, dimensions and reporting

![letamart_prod_analytics dataset](docs/bigquery_prod_analytics.png)

---

## 12. Scheduling & Orchestration

Three GitHub Actions workflows automate the full pipeline:

### dbt CI (`dbt_ci.yml`) — triggered on every PR to main
1. Authenticate to GCP via Workload Identity Federation
2. Install dbt + packages
3. Compile all SQL — catches syntax errors before they reach BigQuery
4. Run source freshness tests
5. Post pass/fail comment on the PR

### Hourly run (`dbt_hourly.yml`) — every hour at :00
1. Authenticate to GCP
2. Check source freshness
3. Run `tag:incremental` models only — fact tables, last 3 days
4. Test incremental models
5. Send Slack alert with pass/fail summary

### Daily full run (`dbt_daily.yml`) — 12:00 UTC every day
1. Authenticate to GCP
2. Check source freshness
3. Run all models in dependency order
4. Run all 127 tests
5. Generate dbt docs — uploaded as GitHub Actions artifact
6. Send inventory Slack alert — out-of-stock and critical products
7. Send run summary Slack alert
8. On failure: send critical failure alert with link to failed run

### GitHub Actions Secrets Required

| Secret | Description |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | WIF provider resource name |
| `GCP_SERVICE_ACCOUNT` | Service account email |
| `GCP_PROJECT_ID` | BigQuery project ID |
| `GCP_DATASET_ID` | Raw dataset ID |
| `GCP_LOCATION` | BigQuery location (EU/US) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

---

## 13. Slack Alerts

Slack alerts fire automatically after every hourly and daily run.

### Run summary alert
Sent after every hourly and daily run — shows pass/fail counts, elapsed time and failed model names.

![Slack alerts firing hourly](docs/slack_alerts.png)

```
✅ letamart_dbt — hourly run ✅ Passed
Models run: 12  |  Passed: 12  |  Errors: 0
Elapsed: 5.5s   |  2026-05-31 16:01 UTC
Project: npd-01  |  Dataset: letamart_raw
```

### Inventory alert
Sent daily with products below reorder point, prioritised by severity:

```
📦 Inventory Alert
🔴 Whole Milk — OUT OF STOCK (dairy | WH-LONDON-01)
🟠 Chicken Breast — CRITICAL (2 units left)
🟡 Sourdough Loaf — low stock (8 units)
```

---

## 14. Key Design Decisions

| Decision | Reason |
|---|---|
| **Separate gcloud configuration** | Personal project never touches the org BigQuery instance |
| **ADC over service account keys** | No key files to accidentally commit to GitHub |
| **Ephemeral intermediate models** | Zero BigQuery storage cost for business logic layer |
| **Incremental merge on facts** | Processes only last 3 days — reduces compute cost by ~95% vs full refresh |
| **Partitioned + clustered fact tables** | Partition pruning and clustering reduce query costs for BI tools |
| **SQLFluff pre-commit hooks** | Consistent SQL style enforced before every commit — no manual review needed |
| **Workload Identity Federation** | Keyless GCP auth from GitHub Actions — no secrets rotation needed |
| **`ON` joins over `USING`** | Explicit join conditions are unambiguous and easier to debug |
| **Column docs in separate `.md` files** | Write once, reference everywhere — single source of truth for column descriptions |
| **`refreshed_at` audit column** | Every staging model tracks when data was last loaded — enables freshness monitoring |
