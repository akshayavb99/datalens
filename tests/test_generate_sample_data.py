import random

import pandas as pd

from datalens.ingest import CANONICAL_COLUMNS, ONLINE_ORDER_COLUMNS, normalize_online_orders
from scripts.generate_sample_data import generate_rows, inject_messiness, write_csv


def test_generate_basic_schema_output(tmp_path):
    rows = generate_rows(10, random.Random(42), schema_type="basic")
    rows = inject_messiness(rows, random.Random(42))
    output_path = tmp_path / "sample.csv"

    write_csv(rows, str(output_path), schema_type="basic")

    generated = pd.read_csv(output_path)
    assert list(generated.columns) == [
        "date",
        "store",
        "category",
        "item",
        "quantity",
        "unit_price",
        "revenue",
    ]


def test_generate_new_schema_output_can_be_reconciled(tmp_path):
    rows = generate_rows(10, random.Random(42), schema_type="new")
    rows = inject_messiness(rows, random.Random(42))
    output_path = tmp_path / "online_orders.csv"

    write_csv(rows, str(output_path), schema_type="new")

    generated = pd.read_csv(output_path)
    assert list(generated.columns) == ONLINE_ORDER_COLUMNS
    
    reconciled = normalize_online_orders(generated)
    assert list(reconciled.columns) == CANONICAL_COLUMNS
    assert len(reconciled) == len(generated)
