"""Functions for converting external exports into DataLens' canonical schema."""

from __future__ import annotations

import pandas as pd


ONLINE_ORDER_COLUMNS = [
    "order_date",
    "store_location",
    "item_category",
    "item_name",
    "item_quantity",
    "order_total",
]

CANONICAL_COLUMNS = [
    "date",
    "store",
    "category",
    "item",
    "quantity",
    "unit_price",
    "revenue",
]


def normalize_online_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Map an online-orders export onto DataLens' canonical sales schema.

    Mapping decisions:
    ``order_date`` is parsed from ``MM/DD/YYYY`` into ``date``;
    ``store_location``, ``item_category``, and ``item_name`` map to
    ``store``, ``category``, and ``item`` respectively; ``item_quantity`` maps
    to ``quantity``; ``order_total`` maps to ``revenue``; and ``unit_price``
    is derived as ``order_total / item_quantity``. Missing categories are
    preserved as missing values so callers can choose whether to drop or fill
    them during cleaning.

    The input is not modified. Invalid dates and numeric values are coerced
    to missing values. A zero or missing item count produces a missing unit
    price.

    Raises:
        ValueError: If one or more required online-order columns are absent.
    """
    missing = [column for column in ONLINE_ORDER_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing online-order columns: {missing}")

    result = pd.DataFrame(index=df.index)
    result["date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y", errors="coerce")
    result["store"] = df["store_location"]
    result["category"] = df["item_category"]
    result["item"] = df["item_name"]
    result["quantity"] = pd.to_numeric(df["item_quantity"], errors="coerce")
    result["revenue"] = pd.to_numeric(df["order_total"], errors="coerce")
    result["unit_price"] = result["revenue"].div(result["quantity"].where(result["quantity"] != 0))

    return result[CANONICAL_COLUMNS].reset_index(drop=True)
