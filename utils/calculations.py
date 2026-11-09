from __future__ import annotations

import pandas as pd


def format_number(value: float | int) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


def format_currency(value: float | int, currency: str = "Dataset price units") -> str:
    if currency == "Dataset price units (currency not provided)":
        return f"{value:,.2f} units"
    symbols = {"USD": "$", "EUR": "€", "INR": "₹"}
    return f"{symbols.get(currency, currency + ' ')}{value:,.2f}"


def event_frame(frame: pd.DataFrame, event_type: str | None = None) -> pd.DataFrame:
    if frame.empty or "event_type" not in frame:
        return frame.copy()
    result = frame.copy()
    if event_type:
        result = result[result["event_type"].astype(str).str.lower().eq(event_type.lower())]
    return result


def funnel_metrics(frame: pd.DataFrame) -> dict[str, float]:
    events = frame.get("event_type", pd.Series(dtype=str)).astype(str).str.lower()
    views = int(events.eq("view").sum())
    carts = int(events.eq("cart").sum())
    purchases = int(events.eq("purchase").sum())
    return {
        "views": views,
        "carts": carts,
        "purchases": purchases,
        "view_to_cart": carts / max(views, 1),
        "cart_to_purchase": purchases / max(carts, 1),
        "cart_abandonment": (carts - purchases) / max(carts, 1),
        "purchase_to_view": purchases / max(views, 1),
    }


def product_label(row: pd.Series) -> str:
    name = row.get("product_name")
    if pd.notna(name) and str(name).strip():
        return str(name)
    brand = row.get("brand")
    category = row.get("category")
    parts = [str(value) for value in [brand, category] if pd.notna(value) and str(value).strip()]
    return " - ".join(parts) if parts else "Unnamed product"


def infer_segment(row: pd.Series) -> str:
    recency, frequency, monetary = row.get("recency", 999), row.get("frequency", 0), row.get("monetary", 0)
    if recency <= 30 and frequency >= 10 and monetary >= 500:
        return "Champions"
    if recency <= 60 and frequency >= 5:
        return "Loyal Customers"
    if recency <= 45 and frequency >= 2:
        return "Potential Loyalists"
    if recency <= 30:
        return "Recent Customers"
    if recency <= 120 and frequency >= 2:
        return "At-Risk Customers"
    return "Lost Customers"


def segment_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    if "segment" in result:
        result["cluster"] = result["segment"]
    if {"recency", "frequency", "monetary", "cluster"}.issubset(result.columns):
        profile = result.groupby("cluster")[["recency", "frequency", "monetary"]].mean()
        scores = profile.rank(pct=True)
        recency = 1 - scores["recency"]
        value = (scores["frequency"] + scores["monetary"]) / 2
        profile_score = (recency + value) / 2
        ordered_clusters = profile_score.sort_values(ascending=False).index.tolist()
        label_order = ["Champions", "Loyal Customers", "Potential Loyalists", "Recent Customers", "At-Risk Customers", "Lost Customers"]
        labels = {cluster: label_order[min(index, len(label_order) - 1)] for index, cluster in enumerate(ordered_clusters)}
        result["segment"] = result["cluster"].map(labels)
    return result
