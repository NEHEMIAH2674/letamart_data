"""
scripts/generate_raw_data.py
-----------------------------
Generates realistic online supermarket data and loads it into BigQuery.
Creates dataset: letamart_raw with 6 tables:
  - orders
  - order_items
  - products
  - customers
  - inventory
  - promotions

Usage:
    python scripts/generate_raw_data.py

Requirements:
    pip install google-cloud-bigquery faker pandas
"""

import random
from datetime import datetime, timedelta, timezone
import pandas as pd
from faker import Faker
from google.cloud import bigquery

# ── Config ────────────────────────────────────────────────────
PROJECT_ID   = "npd-01"
DATASET_ID   = "letamart_raw"
LOCATION     = "EU"

NUM_CUSTOMERS  = 500
NUM_PRODUCTS   = 200
NUM_ORDERS     = 3000
NUM_PROMOTIONS = 20

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

client = bigquery.Client(project=PROJECT_ID)


# ── Helpers ───────────────────────────────────────────────────
def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def create_dataset():
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset_ref.location = LOCATION
    dataset = client.create_dataset(dataset_ref, exists_ok=True)
    print(f"✅ Dataset ready: {dataset.full_dataset_id}")


def load_table(df: pd.DataFrame, table_id: str):
    full_table = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, full_table, job_config=job_config)
    job.result()
    print(f"✅ Loaded {len(df):,} rows → {full_table}")


# ── Generators ────────────────────────────────────────────────

def generate_products() -> pd.DataFrame:
    categories = {
        "fresh_produce":  ["apples", "bananas", "carrots", "broccoli", "spinach",
                           "tomatoes", "potatoes", "onions", "lettuce", "peppers"],
        "dairy":          ["whole milk", "semi-skimmed milk", "cheddar cheese",
                           "greek yogurt", "butter", "cream cheese", "eggs",
                           "sour cream", "mozzarella", "oat milk"],
        "bakery":         ["white bread", "sourdough loaf", "croissants",
                           "bagels", "baguette", "muffins", "crumpets",
                           "hot cross buns", "brioche", "rye bread"],
        "meat_seafood":   ["chicken breast", "beef mince", "salmon fillet",
                           "pork sausages", "bacon rashers", "lamb chops",
                           "cod fillet", "turkey mince", "prawns", "tuna steak"],
        "beverages":      ["orange juice", "apple juice", "sparkling water",
                           "still water", "cola", "lemonade", "green tea",
                           "coffee beans", "hot chocolate", "energy drink"],
        "snacks":         ["crisps", "chocolate bar", "popcorn", "mixed nuts",
                           "cereal bar", "biscuits", "pretzels", "dried mango",
                           "rice cakes", "trail mix"],
        "frozen":         ["frozen peas", "ice cream", "frozen pizza",
                           "fish fingers", "frozen chips", "waffles",
                           "frozen berries", "ready meals", "frozen prawns",
                           "veggie burgers"],
        "household":      ["washing powder", "dishwasher tablets", "bin bags",
                           "toilet roll", "kitchen roll", "washing up liquid",
                           "fabric softener", "bleach", "sponges", "cling film"],
        "personal_care":  ["shampoo", "conditioner", "body wash", "toothpaste",
                           "deodorant", "moisturiser", "lip balm", "razor",
                           "hand soap", "sunscreen"],
        "alcohol":        ["red wine", "white wine", "lager", "pale ale",
                           "gin", "vodka", "prosecco", "whisky", "cider", "rum"],
    }

    brands = ["Tesco", "Sainsbury's", "M&S", "Waitrose", "Organic Valley",
              "Green & Good", "FreshFarm", "PurePick", "BestValue", "Premium Select"]

    rows = []
    product_id = 1
    for category, items in categories.items():
        for item in items:
            is_alcohol = category == "alcohol"
            cost  = round(random.uniform(0.30, 12.00), 2)
            rrp   = round(cost * random.uniform(1.3, 2.5), 2)
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
    tiers    = ["bronze", "silver", "gold", "platinum"]
    tier_wts = [0.5, 0.3, 0.15, 0.05]
    rows = []
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    end   = datetime(2024, 12, 31, tzinfo=timezone.utc)

    for i in range(1, NUM_CUSTOMERS + 1):
        rows.append({
            "customer_id":   f"CUST-{i:05d}",
            "email":         fake.unique.email(),
            "first_name":    fake.first_name(),
            "last_name":     fake.last_name(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
            "registered_at": random_date(start, end).isoformat(),
            "postcode":      fake.postcode(),
            "loyalty_tier":  random.choices(tiers, weights=tier_wts)[0],
            "is_active":     random.random() > 0.08,
            "_loaded_at":    datetime.now(timezone.utc).isoformat(),
        })
    return pd.DataFrame(rows)


def generate_promotions() -> pd.DataFrame:
    promo_types = ["pct_discount", "fixed_discount", "bogo", "free_delivery"]
    rows = []
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)

    for i in range(1, NUM_PROMOTIONS + 1):
        p_type     = random.choice(promo_types)
        valid_from = random_date(start, datetime(2024, 6, 1, tzinfo=timezone.utc))
        valid_to   = valid_from + timedelta(days=random.randint(7, 60))
        rows.append({
            "promo_id":       f"PROMO-{i:03d}",
            "promo_code":     f"SAVE{i:02d}",
            "promo_type":     p_type,
            "discount_value": round(random.uniform(5, 30), 2) if p_type != "free_delivery" else 0,
            "min_basket_gbp": round(random.uniform(10, 50), 2),
            "valid_from":     valid_from.date().isoformat(),
            "valid_to":       valid_to.date().isoformat(),
            "is_active":      random.random() > 0.3,
        })
    return pd.DataFrame(rows)


def generate_orders(customers: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    statuses  = ["pending", "confirmed", "picking", "dispatched", "delivered",
                 "cancelled", "returned"]
    status_wt = [0.02, 0.03, 0.03, 0.05, 0.75, 0.08, 0.04]
    channels  = ["web", "app", "partner"]
    chan_wt   = [0.5, 0.4, 0.1]

    customer_ids = customers["customer_id"].tolist()
    promo_codes  = promotions["promo_code"].tolist() + [None] * 5

    rows = []
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    end   = datetime(2024, 12, 31, tzinfo=timezone.utc)

    for i in range(1, NUM_ORDERS + 1):
        created_at   = random_date(start, end)
        slot_start   = created_at + timedelta(hours=random.randint(2, 48))
        slot_end     = slot_start + timedelta(hours=2)
        rows.append({
            "order_id":            f"ORD-{i:06d}",
            "customer_id":         random.choice(customer_ids),
            "status":              random.choices(statuses, weights=status_wt)[0],
            "channel":             random.choices(channels, weights=chan_wt)[0],
            "created_at":          created_at.isoformat(),
            "delivery_slot_start": slot_start.isoformat(),
            "delivery_slot_end":   slot_end.isoformat(),
            "delivery_address_id": f"ADDR-{random.randint(1, 9999):05d}",
            "promo_code":          random.choice(promo_codes),
            "_loaded_at":          datetime.now(timezone.utc).isoformat(),
        })
    return pd.DataFrame(rows)


def generate_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    product_ids = products["product_id"].tolist()
    rows = []
    item_id = 1

    for _, order in orders.iterrows():
        num_items = random.randint(1, 12)
        chosen    = random.sample(product_ids, min(num_items, len(product_ids)))

        for product_id in chosen:
            product      = products[products["product_id"] == product_id].iloc[0]
            quantity     = random.randint(1, 5)
            unit_price   = round(product["rrp_gbp"] * random.uniform(0.85, 1.05), 2)
            discount     = round(unit_price * random.uniform(0, 0.2), 2) if random.random() > 0.7 else 0
            is_sub       = random.random() > 0.95
            sub_product  = random.choice(product_ids) if is_sub else None

            rows.append({
                "order_item_id":          f"ITEM-{item_id:08d}",
                "order_id":               order["order_id"],
                "product_id":             product_id,
                "quantity":               quantity,
                "unit_price_gbp":         unit_price,
                "discount_amount_gbp":    discount,
                "substituted_product_id": sub_product,
            })
            item_id += 1

    return pd.DataFrame(rows)


def generate_inventory(products: pd.DataFrame) -> pd.DataFrame:
    warehouses = ["WH-LONDON-01", "WH-MANC-01", "WH-BHAM-01", "WH-LEEDS-01"]
    rows = []
    inv_id = 1
    today  = datetime.now(timezone.utc).date()

    for _, product in products.iterrows():
        for warehouse in warehouses:
            on_hand   = random.randint(0, 500)
            reserved  = random.randint(0, min(50, on_hand))
            in_transit = random.randint(0, 100)
            reorder   = random.randint(20, 80)
            rows.append({
                "inventory_id":    f"INV-{inv_id:07d}",
                "product_id":      product["product_id"],
                "warehouse_id":    warehouse,
                "snapshot_date":   today.isoformat(),
                "units_on_hand":   on_hand,
                "units_reserved":  reserved,
                "units_in_transit": in_transit,
                "reorder_point":   reorder,
                "_loaded_at":      datetime.now(timezone.utc).isoformat(),
            })
            inv_id += 1

    return pd.DataFrame(rows)


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🛒 letamart — raw data generator")
    print("=" * 40)

    create_dataset()

    print("\n📦 Generating products...")
    products = generate_products()
    load_table(products, "products")

    print("\n👥 Generating customers...")
    customers = generate_customers()
    load_table(customers, "customers")

    print("\n🎟️  Generating promotions...")
    promotions = generate_promotions()
    load_table(promotions, "promotions")

    print("\n🛍️  Generating orders...")
    orders = generate_orders(customers, promotions)
    load_table(orders, "orders")

    print("\n📋 Generating order items...")
    order_items = generate_order_items(orders, products)
    load_table(order_items, "order_items")

    print("\n🏭 Generating inventory...")
    inventory = generate_inventory(products)
    load_table(inventory, "inventory")

    print("\n✅ All done! letamart_raw is ready in BigQuery.")
    print(f"   Project : {PROJECT_ID}")
    print(f"   Dataset : {DATASET_ID}")
    print(f"   Tables  : products, customers, promotions, orders, order_items, inventory")
