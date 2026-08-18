#!/usr/bin/env python3
"""Generate a synthetic coffee-shop sales dataset for DataLens.

Produces ``data/sample.csv`` with ~800 rows spanning roughly six months of
daily sales across a few stores, categories, and items. A small amount of
messiness (duplicate rows, missing values) is deliberately injected so the
cleaning functions in ``datalens.cleaning`` have real work to do.

Usage:
    python scripts/generate_sample_data.py [--rows 800] [--schema-type basic]
    python scripts/generate_sample_data.py --schema-type new
"""

from __future__ import annotations

import argparse
import os
import random
from datetime import date, timedelta
from pathlib import Path

STORES = ["Downtown", "Riverside", "Uptown", "Airport"]

# category -> [(item, base_unit_price), ...]
CATALOG = {
    "coffee": [
        ("Drip Coffee", 2.75),
        ("Latte", 4.25),
        ("Cappuccino", 4.00),
        ("Espresso", 2.50),
    ],
    "tea": [("Green Tea", 3.00), ("Chai Latte", 4.00), ("Iced Tea", 2.75)],
    "pastry": [("Croissant", 3.25), ("Muffin", 3.00), ("Scone", 3.10)],
    "sandwich": [("Turkey Club", 7.50), ("Veggie Wrap", 6.75), ("BLT", 7.00)],
    "merch": [("Mug", 12.00), ("Bag of Beans", 14.50), ("Gift Card", 25.00)],
}


def generate_rows(
    num_rows: int,
    rng: random.Random,
    schema_type: str = "basic",
) -> list[dict]:
    """Generate rows using either the canonical or online-orders schema."""
    if schema_type not in {"basic", "new"}:
        raise ValueError("schema_type must be either 'basic' or 'new'")

    start_day = date(2026, 1, 1)
    day_span = 180

    rows: list[dict] = []
    for _ in range(num_rows):
        day_offset = rng.randint(0, day_span)
        row_date = start_day + timedelta(days=day_offset)
        # Weekend bump: coffee shops are busier Fri/Sat.
        weekday = row_date.weekday()
        weekend_multiplier = 1.4 if weekday in (4, 5) else 1.0

        category = rng.choice(list(CATALOG.keys()))
        item, base_price = rng.choice(CATALOG[category])
        store = rng.choice(STORES)

        quantity = max(1, round(rng.gauss(3, 1.5) * weekend_multiplier))
        unit_price = round(base_price * rng.uniform(0.95, 1.05), 2)
        revenue = round(unit_price * quantity, 2)

        if schema_type == "basic":
            rows.append(
                {
                    "date": row_date.isoformat(),
                    "store": store,
                    "category": category,
                    "item": item,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "revenue": revenue,
                }
            )
        else:
            rows.append(
                {
                    "order_date": row_date.strftime("%m/%d/%Y"),
                    "store_location": store,
                    "item_category": category,
                    "item_name": item,
                    "item_quantity": quantity,
                    "order_total": revenue,
                }
            )
    return rows


def inject_messiness(rows: list[dict], rng: random.Random) -> list[dict]:
    """Duplicate a handful of rows and null out a handful of values.

    This mimics real-world messy exports so the cleaning functions have
    something to actually clean.
    """
    messy = list(rows)

    # Duplicate ~2% of rows.
    duplicate_count = max(1, len(rows) // 50)
    messy.extend(rng.choice(rows).copy() for _ in range(duplicate_count))

    # Null out a value in ~3% of rows (using fields present in the selected schema).
    if rows and "date" in rows[0]:
        nullable_fields = ["quantity", "unit_price", "store", "category"]
    else:
        nullable_fields = [
            "order_date",
            "store_location",
            "item_category",
            "item_name",
            "item_quantity",
        ]
    missing_count = max(1, len(messy) // 33)
    for _ in range(missing_count):
        idx = rng.randrange(len(messy))
        field = rng.choice(nullable_fields)
        messy[idx] = {**messy[idx], field: ""}

    rng.shuffle(messy)
    return messy


def write_csv(rows: list[dict], output_path: str, schema_type: str = "basic") -> None:
    import csv

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if schema_type == "basic":
        fieldnames = [
            "date",
            "store",
            "category",
            "item",
            "quantity",
            "unit_price",
            "revenue",
        ]
    elif schema_type == "new":
        fieldnames = [
            "order_id",
            "order_date",
            "store_location",
            "item_category",
            "item_name",
            "item_quantity",
            "order_total",
        ]
    else:
        raise ValueError("schema_type must be either 'basic' or 'new'")
    with open(output_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def reconciled_output_path(output_path: str) -> str:
    """Return the sibling path used for a normalized online-orders export."""
    path = Path(output_path)
    suffix = path.suffix or ".csv"
    return str(path.with_name(f"{path.stem}_reconciled{suffix}"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=800, help="Number of base rows to generate.")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument(
        "--schema-type",
        choices=["basic", "new"],
        default="basic",
        help="Dataset schema to generate (default: basic).",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    output_path = args.output or (
        "data/sample.csv" if args.schema_type == "basic" else "data/online_orders.csv"
    )
    rows = generate_rows(args.rows, rng, schema_type=args.schema_type)
    rows = inject_messiness(rows, rng)
    write_csv(rows, output_path, schema_type=args.schema_type)
    print(f"Wrote {len(rows)} rows to {output_path}")

    if args.schema_type == "new":
        import pandas as pd

        from datalens.ingest import normalize_online_orders

        raw_export = pd.read_csv(output_path)
        reconciled = normalize_online_orders(raw_export)
        normalized_path = reconciled_output_path(output_path)
        reconciled.to_csv(normalized_path, index=False)
        print(f"Wrote {len(reconciled)} reconciled rows to {normalized_path}")


if __name__ == "__main__":
    main()
