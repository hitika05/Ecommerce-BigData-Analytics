from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

ROOT = Path(__file__).resolve().parents[1]
try:
    DATA_ROOT = Path(st.secrets["DATA_ROOT"])
except (KeyError, StreamlitSecretNotFoundError):
    DATA_ROOT = ROOT / "data"

ALIASES = {
    "event_time": ["event_time", "timestamp", "event_timestamp", "datetime"],
    "event_type": ["event_type", "event", "type"],
    "user_id": ["user_id", "visitor_id", "customer_id"],
    "product_id": ["product_id", "item_id", "sku"],
    "category": ["category_code", "category", "category_name", "main_category"],
    "brand": ["brand", "brand_name"],
    "price": ["price", "unit_price", "amount"],
    "score": ["score", "rating", "prediction", "recommendation_score"],
    "segment": ["segment", "cluster_label", "customer_segment"],
}


def _read_path(path: Path) -> pd.DataFrame:
    try:
        if path.is_dir():
            parquet = list(path.rglob("*.parquet"))
            csv = list(path.rglob("*.csv"))
            if parquet:
                return pd.read_parquet(path)
            if csv:
                return pd.concat((pd.read_csv(item) for item in csv), ignore_index=True)
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path)
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Could not read {path.name}: {exc}")
    return pd.DataFrame()


def _source_path(name: str) -> Path:
    imported = {
        "analytics": DATA_ROOT / "_imported" / "clean_events",
        "recommendations": DATA_ROOT / "_imported" / "recommendations",
        "segments": DATA_ROOT / "_imported" / "segments",
        "evaluation": DATA_ROOT / "_imported" / "evaluation",
    }.get(name)
    if imported and imported.exists():
        return imported
    return DATA_ROOT / name


@st.cache_data(show_spinner=False)
def load_folder(name: str) -> pd.DataFrame:
    folder = _source_path(name)
    if not folder.exists():
        return pd.DataFrame()
    return _read_path(folder)


def standardize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    lower = {str(column).lower().strip(): column for column in result.columns}
    for standard, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in lower:
                result[standard] = result[lower[candidate]]
                break
    if "event_time" in result:
        result["event_time"] = pd.to_datetime(result["event_time"], errors="coerce")
    for numeric in ["price", "score", "recency", "frequency", "monetary", "quantity"]:
        if numeric in result:
            result[numeric] = pd.to_numeric(result[numeric], errors="coerce")
    return result


@dataclass
class DashboardData:
    analytics: pd.DataFrame = field(default_factory=pd.DataFrame)
    recommendations: pd.DataFrame = field(default_factory=pd.DataFrame)
    segments: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: pd.DataFrame = field(default_factory=pd.DataFrame)
    popularity: pd.DataFrame = field(default_factory=pd.DataFrame)
    evaluation: pd.DataFrame = field(default_factory=pd.DataFrame)
    sample: bool = False

    @property
    def has_any_data(self) -> bool:
        return any(not frame.empty for frame in [self.analytics, self.recommendations, self.segments, self.metadata])

    def with_sample_data(self) -> "DashboardData":
        rng = np.random.default_rng(42)
        dates = pd.date_range("2019-10-01", periods=30, freq="D")
        rows = []
        for date in dates:
            for event, count in [("view", 900), ("cart", 180), ("purchase", 55)]:
                for _ in range(count // 10):
                    rows.append({"event_time": date + pd.Timedelta(hours=int(rng.integers(0, 24))), "event_type": event, "user_id": int(rng.integers(1000, 5000)), "product_id": int(rng.integers(1, 21)), "category": f"category_{int(rng.integers(1, 6))}", "brand": f"brand_{int(rng.integers(1, 8))}", "price": round(float(rng.uniform(15, 350)), 2)})
        analytics = pd.DataFrame(rows)
        segments = pd.DataFrame({"user_id": range(1000, 1200), "recency": rng.integers(1, 60, 200), "frequency": rng.integers(1, 20, 200), "monetary": rng.uniform(50, 2500, 200)})
        metadata = analytics[["product_id", "category", "brand", "price"]].drop_duplicates("product_id")
        return DashboardData(analytics, pd.DataFrame(), segments, metadata, pd.DataFrame(), pd.DataFrame(), True)

    def overview_metrics(self) -> dict[str, float]:
        frame = self.analytics
        purchases = frame[frame.get("event_type", pd.Series(dtype=str)).astype(str).str.lower().eq("purchase")] if not frame.empty else frame
        revenue = float((purchases.get("price", pd.Series(dtype=float)).fillna(0)).sum())
        return {"events": len(frame), "users": frame["user_id"].nunique() if "user_id" in frame else 0, "purchases": len(purchases), "revenue": revenue}

    def readiness(self) -> dict[str, bool]:
        return {"Analytics events": not self.analytics.empty, "Product metadata": not self.metadata.empty, "Customer segments": not self.segments.empty, "Recommendations": not self.recommendations.empty, "Evaluation metrics": not self.evaluation.empty}

    @property
    def currency_label(self) -> str:
        candidates = [column for column in self.analytics.columns if "curr" in str(column).lower()]
        if candidates and self.analytics[candidates[0]].notna().any():
            return str(self.analytics[candidates[0]].dropna().iloc[0])
        return "Dataset price units (currency not provided)"


@st.cache_resource
def load_dashboard_data() -> DashboardData:
    analytics = standardize(load_folder("analytics"))
    recommendations = standardize(load_folder("recommendations"))
    segments = standardize(load_folder("segments"))
    metadata = standardize(load_folder("metadata"))
    evaluation = standardize(load_folder("evaluation"))
    if metadata.empty and not analytics.empty and "product_id" in analytics:
        columns = [column for column in ["product_id", "brand", "category", "price"] if column in analytics]
        metadata = analytics[columns].drop_duplicates("product_id")
    popularity = pd.DataFrame()
    if not analytics.empty and "product_id" in analytics and "event_type" in analytics:
        purchases = analytics[analytics["event_type"].astype(str).str.lower().eq("purchase")]
        popularity = purchases.groupby("product_id").size().reset_index(name="popularity").sort_values("popularity", ascending=False)
    return DashboardData(analytics, recommendations, segments, metadata, popularity, evaluation)
