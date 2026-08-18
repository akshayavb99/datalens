import pandas as pd
import pytest
from datetime import date

from datalens.ingest import normalize_online_orders


def test_normalize_online_orders_maps_columns_and_derives_unit_price():
    source = pd.DataFrame(
        {
            "order_date": ["01/05/2026", "02/14/2026"],
            "store_location": ["Downtown", "Airport"],
            "item_category": ["coffee", "tea"],
            "item_name": ["Latte", "Green Tea"],
            "item_quantity": [2, 1],
            "order_total": [8.50, 3.00],
        }
    )

    result = normalize_online_orders(source)

    assert list(result.columns) == [
        "date",
        "store",
        "category",
        "item",
        "quantity",
        "unit_price",
        "revenue",
    ]
    assert result.loc[0, "date"].date() == date(2026, 1, 5)
    assert result.loc[0, "store"] == "Downtown"
    assert result.loc[0, "category"] == "coffee"
    assert result.loc[0, "item"] == "Latte"
    assert result.loc[0, "quantity"] == 2
    assert result.loc[0, "unit_price"] == pytest.approx(4.25)
    assert result.loc[0, "revenue"] == pytest.approx(8.50)


def test_normalize_online_orders_preserves_missing_category():
    source = pd.DataFrame(
        {
            "order_date": ["03/01/2026"],
            "store_location": ["Riverside"],
            "item_category": [None],
            "item_name": ["Muffin"],
            "item_quantity": [2],
            "order_total": [6.00],
        }
    )

    result = normalize_online_orders(source)

    assert pd.isna(result.loc[0, "category"])
    assert len(result) == 1


def test_normalize_online_orders_coerces_invalid_values_and_zero_count():
    source = pd.DataFrame(
        {
            "order_date": ["not-a-date", "04/01/2026"],
            "store_location": ["Downtown", "Downtown"],
            "item_category": ["coffee", "coffee"],
            "item_name": ["Latte", "Latte"],
            "item_quantity": ["oops", 0],
            "order_total": ["bad", 8.0],
        }
    )

    result = normalize_online_orders(source)

    assert pd.isna(result.loc[0, "date"])
    assert pd.isna(result.loc[0, "quantity"])
    assert pd.isna(result.loc[0, "revenue"])
    assert pd.isna(result.loc[0, "unit_price"])
    assert pd.isna(result.loc[1, "unit_price"])


def test_normalize_online_orders_requires_source_columns():
    source = pd.DataFrame({"order_date": ["01/01/2026"]})

    with pytest.raises(ValueError, match="Missing online-order columns"):
        normalize_online_orders(source)
