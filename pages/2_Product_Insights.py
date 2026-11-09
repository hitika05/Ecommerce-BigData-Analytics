import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_dashboard_data
from utils.calculations import product_label
from utils.visualizations import empty_chart

st.title("Product Insights")
st.caption("Product performance enriched with brand, category, price, and available metadata.")
data = load_dashboard_data()
events = data.analytics
if events.empty:
    st.warning("Analytics exports are unavailable.")
    st.stop()
with st.sidebar:
    brands = st.multiselect("Brand", sorted(events["brand"].dropna().astype(str).unique())) if "brand" in events else []
    categories = st.multiselect("Category", sorted(events["category"].dropna().astype(str).unique())) if "category" in events else []
filtered = events.copy()
if brands: filtered = filtered[filtered["brand"].astype(str).isin(brands)]
if categories: filtered = filtered[filtered["category"].astype(str).isin(categories)]
views = filtered[filtered["event_type"].astype(str).str.lower().eq("view")]
purchases = filtered[filtered["event_type"].astype(str).str.lower().eq("purchase")]
def product_table(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    group = [col for col in ["product_id", "brand", "category", "price"] if col in frame]
    if not group: return pd.DataFrame()
    result = frame.groupby(group, dropna=False).size().reset_index(name=metric).sort_values(metric, ascending=False).head(10)
    result["Product"] = result.apply(product_label, axis=1)
    return result
left, right = st.columns(2)
with left:
    top_views = product_table(views, "views")
    st.plotly_chart(px.bar(top_views, x="views", y="Product", orientation="h", hover_data=["product_id"], title="Top 10 most viewed products") if not top_views.empty else empty_chart(), use_container_width=True)
with right:
    top_purchases = product_table(purchases, "purchases")
    st.plotly_chart(px.bar(top_purchases, x="purchases", y="Product", orientation="h", hover_data=["product_id"], title="Top 10 most purchased products") if not top_purchases.empty else empty_chart(), use_container_width=True)
left, right = st.columns(2)
with left:
    revenue = purchases.groupby([c for c in ["product_id", "brand", "category"] if c in purchases], dropna=False)["price"].sum().reset_index(name="revenue").nlargest(10, "revenue")
    if not revenue.empty:
        revenue["Product"] = revenue.apply(product_label, axis=1)
        st.plotly_chart(px.bar(revenue, x="revenue", y="Product", orientation="h", hover_data=["product_id"], title="Revenue by product"), use_container_width=True)
    else:
        st.plotly_chart(empty_chart(), use_container_width=True)
with right:
    by_brand = purchases.groupby("brand", dropna=False)["price"].sum().reset_index(name="revenue").nlargest(10, "revenue") if "brand" in purchases else pd.DataFrame()
    st.plotly_chart(px.bar(by_brand, x="revenue", y="brand", orientation="h", title="Revenue by brand") if not by_brand.empty else empty_chart(), use_container_width=True)
