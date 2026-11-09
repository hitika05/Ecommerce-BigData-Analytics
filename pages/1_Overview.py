import pandas as pd
import streamlit as st
import plotly.express as px

from utils.calculations import event_frame, format_currency, format_number, funnel_metrics
from utils.data_loader import load_dashboard_data
from utils.visualizations import empty_chart

st.title("Executive Overview")
st.caption("A concise view of customer activity, conversion, and commercial performance.")
data = load_dashboard_data()
frame = data.analytics.copy()
if frame.empty:
    st.warning("Analytics exports are unavailable. Add processed event Parquet files to `data/analytics`.")
    st.stop()

with st.expander("Filters", expanded=True):
    a, b, c = st.columns(3)
    dates = pd.to_datetime(frame["event_time"], errors="coerce").dt.date if "event_time" in frame else None
    date_range = a.date_input("Date range", (dates.min(), dates.max())) if dates is not None and dates.notna().any() else None
    category = b.multiselect("Category", sorted(frame["category"].dropna().astype(str).unique())) if "category" in frame else []
    events = c.multiselect("Event type", sorted(frame["event_type"].dropna().astype(str).unique()), default=sorted(frame["event_type"].dropna().astype(str).unique())) if "event_type" in frame else []
filtered = frame.copy()
if date_range and len(date_range) == 2 and "event_time" in filtered:
    filtered = filtered[filtered["event_time"].dt.date.between(date_range[0], date_range[1])]
if category and "category" in filtered:
    filtered = filtered[filtered["category"].astype(str).isin(category)]
if events and "event_type" in filtered:
    filtered = filtered[filtered["event_type"].astype(str).isin(events)]
purchases = event_frame(filtered, "purchase")
metrics = [("Total events", len(filtered)), ("Unique users", filtered["user_id"].nunique() if "user_id" in filtered else 0), ("Purchases", len(purchases)), ("Revenue", format_currency(purchases["price"].sum() if "price" in purchases else 0, data.currency_label))]
for col, (label, value) in zip(st.columns(4), metrics):
    col.metric(label, value)

left, right = st.columns(2)
with left:
    if "event_time" in filtered:
        daily = filtered.assign(day=filtered["event_time"].dt.date).groupby(["day", "event_type"], as_index=False).size()
        st.plotly_chart(px.area(daily, x="day", y="size", color="event_type", title="Daily event volume"), use_container_width=True)
    else:
        st.plotly_chart(empty_chart(), use_container_width=True)
with right:
    if not purchases.empty and "event_time" in purchases:
        revenue = purchases.assign(day=purchases["event_time"].dt.date).groupby("day", as_index=False)["price"].sum()
        st.plotly_chart(px.line(revenue, x="day", y="price", title="Revenue trend", markers=True), use_container_width=True)
    else:
        st.plotly_chart(empty_chart("No purchase revenue available"), use_container_width=True)
left, right = st.columns(2)
with left:
    counts = filtered["event_type"].value_counts().rename_axis("event_type").reset_index(name="events")
    st.plotly_chart(
        px.pie(counts, names="event_type", values="events", hole=.5, title="Event distribution"),
        use_container_width=True,
    )
with right:
    funnel = filtered["event_type"].value_counts().reindex(["view", "cart", "purchase"]).fillna(0).reset_index()
    funnel.columns = ["event_type", "events"]
    st.plotly_chart(
        px.funnel(funnel, y="event_type", x="events", title="Conversion funnel"),
        use_container_width=True,
    )

if "category" in purchases:
    left, right = st.columns(2)
    with left:
        category_revenue = (
            purchases.groupby("category", as_index=False)["price"]
            .sum()
            .nlargest(5, "price")
            .sort_values("price", ascending=True)
        )
        st.plotly_chart(
            px.bar(
                category_revenue,
                x="price",
                y="category",
                orientation="h",
                text="price",
                labels={"price": data.currency_label, "category": "Category"},
                title="Top 5 Categories by Revenue",
            ).update_traces(texttemplate="%{text:,.0f}", textposition="outside"),
            use_container_width=True,
        )
    with right:
        if "brand" in purchases:
            brand_values = purchases["brand"].astype("string").str.strip()
            brand_revenue = (
                purchases.loc[brand_values.notna() & brand_values.ne(""), ["brand", "price"]]
                .assign(brand=lambda frame: frame["brand"].astype("string").str.strip())
                .groupby("brand", as_index=False)["price"]
                .sum()
                .nlargest(10, "price")
                .sort_values("price", ascending=True)
            )
            brand_revenue["brand"] = brand_revenue["brand"].replace(
                {"unknown": "Unknown", "UNKNOWN": "Unknown"}
            )
        else:
            brand_revenue = pd.DataFrame()
        if brand_revenue.empty:
            st.plotly_chart(empty_chart("No non-blank brand revenue available"), use_container_width=True)
        else:
            st.plotly_chart(
                px.bar(
                    brand_revenue,
                    x="price",
                    y="brand",
                    orientation="h",
                    text="price",
                    labels={"price": data.currency_label, "brand": "Brand"},
                    title="Top 10 Brands by Revenue",
                ).update_traces(texttemplate="%{text:,.0f}", textposition="outside"),
                use_container_width=True,
            )

st.markdown("### Automated business insights")
funnel_metrics_for_view = funnel_metrics(filtered)
st.info(f"Purchase-to-view conversion is **{funnel_metrics_for_view['purchase_to_view']:.2%}** across the selected period. Revenue uses the `price` field in {data.currency_label.lower()}.")
