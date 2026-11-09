import plotly.express as px
import streamlit as st

from utils.data_loader import load_dashboard_data
from utils.calculations import funnel_metrics
from utils.visualizations import empty_chart

st.title("Business Intelligence")
st.caption("Decision metrics and recommendations grounded in the exported event analytics.")
events = load_dashboard_data().analytics
if events.empty:
    st.warning("Analytics exports are unavailable.")
    st.stop()
kind = events["event_type"].astype(str).str.lower()
views, carts, purchases = (events[kind.eq(name)] for name in ["view", "cart", "purchase"])
funnel = funnel_metrics(events)
view_cart = funnel["view_to_cart"]
cart_purchase = funnel["cart_to_purchase"]
abandonment = funnel["cart_abandonment"]
for col, (label, value) in zip(st.columns(3), [("Cart abandonment", abandonment), ("View-to-cart", view_cart), ("Cart-to-purchase", cart_purchase)]):
    col.metric(label, f"{value:.2%}")
if "event_time" in events:
    hourly = events.assign(hour=events["event_time"].dt.hour).groupby("hour").size().reset_index(name="events")
    st.plotly_chart(px.bar(hourly, x="hour", y="events", title="Peak shopping hours"), use_container_width=True)
    daily = events.assign(day=events["event_time"].dt.date).groupby("day").size().reset_index(name="events")
    st.plotly_chart(px.line(daily, x="day", y="events", markers=True, title="Daily shopping trends"), use_container_width=True)
left, right = st.columns(2)
with left:
    if "category" in purchases:
        category = (
            purchases.groupby("category", dropna=False)["price"]
            .sum()
            .reset_index(name="revenue")
            .nlargest(10, "revenue")
            .sort_values("revenue", ascending=True)
        )
    else:
        category = None
    if category is not None and not category.empty:
        category_chart = px.bar(
            category,
            x="revenue",
            y="category",
            orientation="h",
            text="revenue",
            labels={"revenue": "Price units", "category": "Category"},
            title="Top 10 Categories by Revenue",
        )
        category_chart.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        category_chart.update_layout(height=480, margin={"l": 10, "r": 30, "t": 55, "b": 35})
        st.plotly_chart(category_chart, use_container_width=True)
    else:
        st.plotly_chart(empty_chart("No category revenue available"), use_container_width=True)
with right:
    if "brand" in purchases:
        brand_values = purchases["brand"].astype("string").str.strip()
        brand = (
            purchases.loc[brand_values.notna() & brand_values.ne(""), ["brand", "price"]]
            .assign(brand=lambda frame: frame["brand"].astype("string").str.strip())
            .groupby("brand", as_index=False)["price"]
            .sum()
            .nlargest(10, "price")
            .sort_values("price", ascending=True)
        )
        brand["brand"] = brand["brand"].replace({"unknown": "Unknown", "UNKNOWN": "Unknown"})
    else:
        brand = None
    if brand is not None and not brand.empty:
        brand_chart = px.bar(
            brand,
            x="price",
            y="brand",
            orientation="h",
            text="price",
            labels={"price": "Price units", "brand": "Brand"},
            title="Top 10 Brands by Revenue",
        )
        brand_chart.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        brand_chart.update_layout(height=480, margin={"l": 10, "r": 30, "t": 55, "b": 35})
        st.plotly_chart(brand_chart, use_container_width=True)
    else:
        st.plotly_chart(empty_chart("No brand revenue available"), use_container_width=True)
st.markdown("### Recommended actions")
st.write(f"- Prioritize checkout friction reduction: **{abandonment:.1%}** of carts do not reach purchase in the selected export.")
if "event_time" in events:
    peak_hour = hourly.loc[hourly["events"].idxmax(), "hour"]
    st.write(f"- Focus merchandising and inventory around the busiest hour (**{peak_hour}:00**).")
else:
    st.write("- Add event timestamps to the analytics export to identify peak shopping hours.")
st.write("- Use Champions and Loyal Customers from the segmentation page for retention campaigns, and test targeted offers for At-Risk Customers.")
