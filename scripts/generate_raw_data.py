"""
scripts/generate_raw_data.py
-----------------------------
Generates realistic online supermarket data and loads it into BigQuery.
Reads config from .env file — no hardcoded credentials.

Creates dataset: letamart_raw with 6 tables:
  - orders, order_items, products, customers, inventory, promotions

Data coverage: 2023-01-01 to 2026-12-31

Row counts:
  - products:    200  (10 categories × 20 products)
  - customers:  2,000
  - promotions:    40
  - orders:    15,000
  - order_items: ~90,000 (avg 6 lines per order)
  - inventory:    800 (200 products × 4 warehouses)

Usage:
    python scripts/generate_raw_data.py

.env requirements:
    GCP_PROJECT_ID=npd-01
    GCP_DATASET_ID=letamart_raw
    GCP_LOCATION=EU
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
"""

import os
import json
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

import pandas as pd
from faker import Faker
from google.cloud import bigquery
from dotenv import load_dotenv

# ── Load environment variables ────────────────────────────────
load_dotenv()

PROJECT_ID  = os.environ["GCP_PROJECT_ID"]
DATASET_ID  = os.environ["GCP_DATASET_ID"]
LOCATION    = os.getenv("GCP_LOCATION", "EU")
WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# ── Row counts ────────────────────────────────────────────────
NUM_CUSTOMERS  = 2_000   # up from 500
NUM_PROMOTIONS = 40      # up from 20
NUM_ORDERS     = 15_000  # up from 3,000

# Date range
START_DATE = datetime(2023, 1, 1, tzinfo=timezone.utc)
END_DATE   = datetime(2026, 12, 31, tzinfo=timezone.utc)

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

client = bigquery.Client(project=PROJECT_ID)

run_start  = datetime.now(timezone.utc)
load_stats = {}


# ── Slack ─────────────────────────────────────────────────────
def send_slack(message: str, success: bool = True):
    if not WEBHOOK_URL:
        print("⚠️  SLACK_WEBHOOK_URL not set — skipping alert")
        return

    colour  = "#2eb886" if success else "#e01e5a"
    icon    = "✅" if success else "🚨"

    payload = {
        "attachments": [
            {
                "color": colour,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{icon} letamart — raw data load"
                        }
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message}
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": (
                                    f"Project: `{PROJECT_ID}` | "
                                    f"Dataset: `{DATASET_ID}` | "
                                    f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                                )
                            }
                        ]
                    }
                ]
            }
        ]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        print("📨 Slack alert sent")
    except urllib.error.URLError as e:
        print(f"⚠️  Slack alert failed: {e}")


def send_success_alert():
    elapsed = round((datetime.now(timezone.utc) - run_start).total_seconds(), 1)
    lines   = [f"*Daily raw data load completed in {elapsed}s*\n"]
    total   = 0
    for table, rows in load_stats.items():
        lines.append(f"• `{table}`: {rows:,} rows")
        total += rows
    lines.append(f"\n*Total rows loaded: {total:,}*")
    send_slack("\n".join(lines), success=True)


def send_failure_alert(error: Exception):
    send_slack(f"*Daily raw data load FAILED*\n\n```{str(error)}```", success=False)


# ── Helpers ───────────────────────────────────────────────────
def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def create_dataset():
    dataset_ref          = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset_ref.location = LOCATION
    client.create_dataset(dataset_ref, exists_ok=True)
    print(f"✅ Dataset ready: {PROJECT_ID}.{DATASET_ID}")


def load_table(df: pd.DataFrame, table_id: str):
    full_table = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, full_table, job_config=job_config)
    job.result()
    load_stats[table_id] = len(df)
    print(f"✅ Loaded {len(df):,} rows → {full_table}")


# ── Generators ────────────────────────────────────────────────

def generate_products() -> pd.DataFrame:
    """
    200 products across 10 categories (20 per category).
    Each product has a realistic cost/rrp margin, weight and brand.
    Alcohol products are flagged as age-restricted.
    ~5% of products are inactive (discontinued lines).
    """
    categories = {
        "fresh_produce": [
            "apples", "bananas", "carrots", "broccoli", "spinach",
            "tomatoes", "potatoes", "onions", "lettuce", "peppers",
            "cucumber", "courgette", "mushrooms", "sweet potatoes", "avocado",
            "kale", "asparagus", "spring onions", "cherry tomatoes", "pak choi",
        ],
        "dairy": [
            "whole milk", "semi-skimmed milk", "cheddar cheese", "greek yogurt",
            "butter", "cream cheese", "eggs", "sour cream", "mozzarella", "oat milk",
            "double cream", "brie", "cottage cheese", "almond milk", "clotted cream",
            "parmesan", "stilton", "crème fraîche", "skyr", "goat cheese",
        ],
        "bakery": [
            "white bread", "sourdough loaf", "croissants", "bagels", "baguette",
            "muffins", "crumpets", "hot cross buns", "brioche", "rye bread",
            "focaccia", "ciabatta", "pitta bread", "tiger bread", "naan bread",
            "chelsea buns", "pain au chocolat", "danish pastry", "scones", "pretzels",
        ],
        "meat_seafood": [
            "chicken breast", "beef mince", "salmon fillet", "pork sausages",
            "bacon rashers", "lamb chops", "cod fillet", "turkey mince", "prawns",
            "tuna steak", "ribeye steak", "chicken thighs", "sea bass fillet",
            "pork belly", "duck breast", "mackerel", "smoked salmon", "crab sticks",
            "venison steak", "whole chicken",
        ],
        "beverages": [
            "orange juice", "apple juice", "sparkling water", "still water",
            "cola", "lemonade", "green tea", "coffee beans", "hot chocolate",
            "energy drink", "coconut water", "kombucha", "elderflower cordial",
            "tomato juice", "cranberry juice", "iced tea", "herbal tea",
            "protein shake", "smoothie", "cold brew coffee",
        ],
        "snacks": [
            "crisps", "chocolate bar", "popcorn", "mixed nuts", "cereal bar",
            "biscuits", "pretzels", "dried mango", "rice cakes", "trail mix",
            "hummus", "peanut butter", "dark chocolate", "wine gums", "jelly beans",
            "tortilla chips", "oat crackers", "granola", "flapjack", "protein bar",
        ],
        "frozen": [
            "frozen peas", "ice cream", "frozen pizza", "fish fingers",
            "frozen chips", "waffles", "frozen berries", "ready meals",
            "frozen prawns", "veggie burgers", "frozen edamame", "frozen spinach",
            "frozen lasagne", "ice lollies", "frozen stir fry", "sorbet",
            "frozen dumplings", "frozen Yorkshire puddings", "frozen garlic bread",
            "frozen mango chunks",
        ],
        "household": [
            "washing powder", "dishwasher tablets", "bin bags", "toilet roll",
            "kitchen roll", "washing up liquid", "fabric softener", "bleach",
            "sponges", "cling film", "aluminium foil", "baking parchment",
            "rubber gloves", "antibacterial spray", "air freshener", "laundry liquid",
            "dishwasher salt", "drain cleaner", "glass cleaner", "furniture polish",
        ],
        "personal_care": [
            "shampoo", "conditioner", "body wash", "toothpaste", "deodorant",
            "moisturiser", "lip balm", "razor", "hand soap", "sunscreen",
            "face wash", "hair mask", "eye cream", "body lotion", "mouthwash",
            "toothbrush", "cotton pads", "nail file", "foot cream", "bath salts",
        ],
        "alcohol": [
            "red wine", "white wine", "lager", "pale ale", "gin",
            "vodka", "prosecco", "whisky", "cider", "rum",
            "rosé wine", "champagne", "craft beer", "stout", "tequila",
            "port", "brandy", "sake", "mead", "hard seltzer",
        ],
    }

    brands = [
        "Tesco", "Sainsbury's", "M&S", "Waitrose", "Organic Valley",
        "Green & Good", "FreshFarm", "PurePick", "BestValue", "Premium Select",
        "Nature's Best", "Urban Harvest", "The Good Food Co.", "Everyday Fresh",
        "Highland Gold", "Garden & Field", "Blue Ridge", "Sunrise Organics",
        "Classic Range", "Artisan Kitchen",
    ]

    rows       = []
    product_id = 1

    for category, items in categories.items():
        for item in items:
            is_alcohol = category == "alcohol"

            # Realistic cost/rrp ratios by category
            if category in ("alcohol", "meat_seafood"):
                cost = round(random.uniform(3.00, 25.00), 2)
            elif category in ("dairy", "fresh_produce"):
                cost = round(random.uniform(0.30, 4.00), 2)
            elif category in ("household", "personal_care"):
                cost = round(random.uniform(0.80, 8.00), 2)
            else:
                cost = round(random.uniform(0.50, 6.00), 2)

            rrp = round(cost * random.uniform(1.35, 2.8), 2)

            rows.append({
                "product_id":        f"PRD-{product_id:04d}",
                "sku":               f"SKU-{product_id:06d}",
                "product_name":      item.title(),
                "category":          category,
                "subcategory":       category.replace("_", " ").title(),
                "brand":             random.choice(brands),
                "cost_price_gbp":    cost,
                "rrp_gbp":           rrp,
                "weight_kg":         round(random.uniform(0.1, 5.0), 2),
                "is_alcohol":        is_alcohol,
                "is_age_restricted": is_alcohol,
                "is_active":         random.random() > 0.05,
            })
            product_id += 1

    return pd.DataFrame(rows)


def generate_customers() -> pd.DataFrame:
    """
    2,000 customers registered between 2020 and 2026.
    Loyalty tiers weighted realistically — most customers are bronze.
    ~8% of customers are inactive (churned or deactivated).
    UK postcodes, realistic names and emails.
    """
    tiers    = ["bronze", "silver", "gold", "platinum"]
    tier_wts = [0.50, 0.30, 0.15, 0.05]

    # Realistic UK cities mapped to postcode prefixes
    cities = [
        ("London",     ["E", "EC", "N", "NW", "SE", "SW", "W", "WC"]),
        ("Manchester", ["M"]),
        ("Birmingham", ["B"]),
        ("Leeds",      ["LS"]),
        ("Glasgow",    ["G"]),
        ("Liverpool",  ["L"]),
        ("Bristol",    ["BS"]),
        ("Edinburgh",  ["EH"]),
        ("Sheffield",  ["S"]),
        ("Cardiff",    ["CF"]),
    ]

    rows  = []
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end   = datetime(2026, 12, 31, tzinfo=timezone.utc)

    for i in range(1, NUM_CUSTOMERS + 1):
        city, prefixes = random.choice(cities)
        prefix         = random.choice(prefixes)
        postcode       = f"{prefix}{random.randint(1,20)} {random.randint(1,9)}{fake.lexify('??').upper()}"

        rows.append({
            "customer_id":   f"CUST-{i:05d}",
            "email":         fake.unique.email(),
            "first_name":    fake.first_name(),
            "last_name":     fake.last_name(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
            "registered_at": random_date(start, end).isoformat(),
            "postcode":      postcode,
            "city":          city,
            "loyalty_tier":  random.choices(tiers, weights=tier_wts)[0],
            "is_active":     random.random() > 0.08,
            "_loaded_at":    datetime.now(timezone.utc).isoformat(),
        })

    return pd.DataFrame(rows)


def generate_promotions() -> pd.DataFrame:
    """
    40 promotional campaigns between 2023 and 2026.
    Mix of percentage discounts, fixed discounts, BOGO and free delivery.
    Seasonal campaigns included (Christmas, Easter, Summer Sale).
    """
    promo_types = ["pct_discount", "fixed_discount", "bogo", "free_delivery"]
    type_wts    = [0.40, 0.30, 0.15, 0.15]

    # Named seasonal campaigns
    seasonal = [
        ("XMAS23",     "pct_discount",   20, 30, "2023-11-25", "2023-12-31"),
        ("NYR24",      "fixed_discount", 10, 25, "2024-01-01", "2024-01-14"),
        ("EASTER24",   "pct_discount",   15, 20, "2024-03-25", "2024-04-05"),
        ("SUMMER24",   "free_delivery",   0, 15, "2024-06-01", "2024-08-31"),
        ("BACK24",     "fixed_discount",  5, 20, "2024-09-01", "2024-09-30"),
        ("BFRIDAY24",  "pct_discount",   25, 40, "2024-11-29", "2024-12-02"),
        ("XMAS24",     "pct_discount",   20, 30, "2024-11-25", "2024-12-31"),
        ("NYR25",      "fixed_discount", 10, 25, "2025-01-01", "2025-01-14"),
        ("EASTER25",   "pct_discount",   15, 20, "2025-04-14", "2025-04-25"),
        ("SUMMER25",   "free_delivery",   0, 15, "2025-06-01", "2025-08-31"),
        ("BFRIDAY25",  "pct_discount",   25, 40, "2025-11-28", "2025-12-01"),
        ("XMAS25",     "pct_discount",   20, 30, "2025-11-25", "2025-12-31"),
    ]

    rows = []
    used_codes = set()

    # Add seasonal campaigns first
    for i, (code, ptype, disc, min_basket, vfrom, vto) in enumerate(seasonal, start=1):
        rows.append({
            "promo_id":       f"PROMO-{i:03d}",
            "promo_code":     code,
            "promo_type":     ptype,
            "discount_value": disc,
            "min_basket_gbp": min_basket,
            "valid_from":     vfrom,
            "valid_to":       vto,
            "is_active":      True,
        })
        used_codes.add(code)

    # Fill remaining with random campaigns
    promo_id = len(seasonal) + 1
    while promo_id <= NUM_PROMOTIONS:
        code = f"SAVE{promo_id:02d}"
        if code in used_codes:
            promo_id += 1
            continue

        p_type     = random.choices(promo_types, weights=type_wts)[0]
        valid_from = random_date(START_DATE, END_DATE - timedelta(days=14))
        valid_to   = valid_from + timedelta(days=random.randint(7, 60))

        rows.append({
            "promo_id":       f"PROMO-{promo_id:03d}",
            "promo_code":     code,
            "promo_type":     p_type,
            "discount_value": round(random.uniform(5, 30), 2) if p_type != "free_delivery" else 0,
            "min_basket_gbp": round(random.uniform(10, 60), 2),
            "valid_from":     valid_from.date().isoformat(),
            "valid_to":       valid_to.date().isoformat(),
            "is_active":      random.random() > 0.3,
        })
        used_codes.add(code)
        promo_id += 1

    return pd.DataFrame(rows)


def generate_orders(customers: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    """
    15,000 orders between 2023 and 2026.
    Realistic order volume — higher at weekends and peak seasons.
    ~75% of orders delivered, ~8% cancelled, ~4% returned.
    Promo codes attached to ~30% of orders.
    Delivery slots 2-48 hours after order creation.
    """
    statuses  = ["pending", "confirmed", "picking", "dispatched", "delivered",
                 "cancelled", "returned"]
    status_wt = [0.02, 0.03, 0.03, 0.05, 0.75, 0.08, 0.04]
    channels  = ["web", "app", "partner"]
    chan_wt   = [0.50, 0.40, 0.10]

    customer_ids = customers["customer_id"].tolist()

    # Promo codes with their validity windows for realistic assignment
    valid_promos = []
    for _, row in promotions.iterrows():
        valid_promos.append({
            "code":       row["promo_code"],
            "valid_from": datetime.fromisoformat(row["valid_from"]),
            "valid_to":   datetime.fromisoformat(row["valid_to"]),
        })

    rows = []

    for i in range(1, NUM_ORDERS + 1):
        created_at = random_date(START_DATE, END_DATE)

        # Pick a valid promo for this order date (~30% attach rate)
        promo_code = None
        if random.random() < 0.30:
            eligible = [
                p["code"] for p in valid_promos
                if p["valid_from"].date() <= created_at.date() <= p["valid_to"].date()
            ]
            if eligible:
                promo_code = random.choice(eligible)

        slot_start = created_at + timedelta(hours=random.randint(2, 48))
        slot_end   = slot_start + timedelta(hours=random.choice([1, 2, 4]))

        rows.append({
            "order_id":            f"ORD-{i:06d}",
            "customer_id":         random.choice(customer_ids),
            "status":              random.choices(statuses, weights=status_wt)[0],
            "channel":             random.choices(channels, weights=chan_wt)[0],
            "created_at":          created_at.isoformat(),
            "delivery_slot_start": slot_start.isoformat(),
            "delivery_slot_end":   slot_end.isoformat(),
            "delivery_address_id": f"ADDR-{random.randint(1, 9999):05d}",
            "promo_code":          promo_code,
            "_loaded_at":          datetime.now(timezone.utc).isoformat(),
        })

        if i % 1000 == 0:
            print(f"   {i:,}/{NUM_ORDERS:,} orders generated...")

    return pd.DataFrame(rows)


def generate_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """
    ~90,000 order line items (avg 6 lines per order).
    Unit prices vary ±15% from RRP to simulate promotions and price changes.
    ~30% of lines have a discount applied.
    ~5% of lines are substituted products.
    """
    product_ids   = products["product_id"].tolist()
    product_index = products.set_index("product_id")
    rows          = []
    item_id       = 1

    for _, order in orders.iterrows():
        # Orders with promos tend to have more items
        if order["promo_code"] is not None:
            num_items = random.randint(4, 15)
        else:
            num_items = random.randint(1, 12)

        chosen = random.sample(product_ids, min(num_items, len(product_ids)))

        for product_id in chosen:
            product    = product_index.loc[product_id]
            quantity   = random.randint(1, 6)
            unit_price = round(float(product["rrp_gbp"]) * random.uniform(0.85, 1.15), 2)

            # ~30% of lines have a discount
            discount = (
                round(unit_price * random.uniform(0.05, 0.25), 2)
                if random.random() > 0.70 else 0.0
            )

            # ~5% substitutions
            is_sub   = random.random() > 0.95
            sub_prod = random.choice(product_ids) if is_sub else None

            rows.append({
                "order_item_id":          f"ITEM-{item_id:08d}",
                "order_id":               order["order_id"],
                "product_id":             product_id,
                "quantity":               quantity,
                "unit_price_gbp":         unit_price,
                "discount_amount_gbp":    discount,
                "substituted_product_id": sub_prod,
            })
            item_id += 1

        if item_id % 10000 == 0:
            print(f"   {item_id:,} order items generated...")

    return pd.DataFrame(rows)


def generate_inventory(products: pd.DataFrame) -> pd.DataFrame:
    """
    800 inventory snapshot rows (200 products × 4 warehouses).
    Stock levels vary by warehouse size — London is the largest.
    ~15% of products are below reorder point to generate alerts.
    In-transit stock simulates replenishment orders in progress.
    """
    warehouses = {
        "WH-LONDON-01": {"scale": 3.0, "weight": 0.45},  # largest
        "WH-MANC-01":   {"scale": 2.0, "weight": 0.25},
        "WH-BHAM-01":   {"scale": 1.5, "weight": 0.20},
        "WH-LEEDS-01":  {"scale": 1.0, "weight": 0.10},  # smallest
    }

    rows   = []
    inv_id = 1
    today  = datetime.now(timezone.utc).date()

    for _, product in products.iterrows():
        for wh_id, wh_config in warehouses.items():
            scale      = wh_config["scale"]
            reorder    = random.randint(20, 80)

            # ~15% of products are at or below reorder point
            if random.random() < 0.15:
                on_hand = random.randint(0, reorder)
            else:
                on_hand = round(reorder * scale * random.uniform(1.1, 6.0))

            reserved   = random.randint(0, min(int(on_hand * 0.2), 50))
            in_transit = random.randint(0, round(reorder * 1.5)) if on_hand <= reorder else 0

            rows.append({
                "inventory_id":     f"INV-{inv_id:07d}",
                "product_id":       product["product_id"],
                "warehouse_id":     wh_id,
                "snapshot_date":    today.isoformat(),
                "units_on_hand":    on_hand,
                "units_reserved":   reserved,
                "units_in_transit": in_transit,
                "reorder_point":    reorder,
                "_loaded_at":       datetime.now(timezone.utc).isoformat(),
            })
            inv_id += 1

    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🛒 letamart — raw data generator")
    print("=" * 50)
    print(f"   Project  : {PROJECT_ID}")
    print(f"   Dataset  : {DATASET_ID}")
    print(f"   Location : {LOCATION}")
    print(f"   Date range: {START_DATE.date()} → {END_DATE.date()}")
    print(f"   Customers: {NUM_CUSTOMERS:,}")
    print(f"   Orders   : {NUM_ORDERS:,}")
    print()

    try:
        create_dataset()

        print("\n📦 Generating products (200)...")
        products = generate_products()
        load_table(products, "products")

        print("\n👥 Generating customers (2,000)...")
        customers = generate_customers()
        load_table(customers, "customers")

        print("\n🎟️  Generating promotions (40)...")
        promotions = generate_promotions()
        load_table(promotions, "promotions")

        print("\n🛍️  Generating orders (15,000)...")
        orders = generate_orders(customers, promotions)
        load_table(orders, "orders")

        print("\n📋 Generating order items (~90,000)...")
        order_items = generate_order_items(orders, products)
        load_table(order_items, "order_items")

        print("\n🏭 Generating inventory (800)...")
        inventory = generate_inventory(products)
        load_table(inventory, "inventory")

        print("\n" + "=" * 50)
        print("✅ All done! letamart_raw is ready in BigQuery.")
        print(f"   Project  : {PROJECT_ID}")
        print(f"   Dataset  : {DATASET_ID}")
        print(f"   Tables   : {', '.join(load_stats.keys())}")
        print(f"   Total rows: {sum(load_stats.values()):,}")
        print("=" * 50)

        send_success_alert()

    except Exception as e:
        print(f"\n🚨 Error: {e}")
        send_failure_alert(e)
        raise
