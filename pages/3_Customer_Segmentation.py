import plotly.express as px
import streamlit as st

from utils.calculations import segment_frame
from utils.data_loader import load_dashboard_data
from utils.visualizations import empty_chart

st.title("Customer Segmentation")
st.caption("RFM outputs from the PySpark pipeline, with labels derived from behavior rather than cluster IDs.")
segments = segment_frame(load_dashboard_data().segments)
if segments.empty:
    st.warning("Segment exports are unavailable. Add the RFM/K-Means Parquet output to `data/segments`.")
    st.stop()
counts = segments["segment"].value_counts().rename_axis("segment").reset_index(name="customers")
counts["percentage"] = counts["customers"] / counts["customers"].sum()
for col, (label, value) in zip(st.columns(3), [("Customers", len(segments)), ("Avg. recency", segments["recency"].mean() if "recency" in segments else 0), ("Avg. monetary", segments["monetary"].mean() if "monetary" in segments else 0)]):
    col.metric(label, f"{value:,.1f}" if isinstance(value, float) else f"{value:,}")
left, right = st.columns(2)
with left:
    st.plotly_chart(px.bar(counts, x="customers", y="segment", orientation="h", title="Customer count by segment"), use_container_width=True)
with right:
    st.plotly_chart(px.pie(counts, names="segment", values="customers", hole=.45, title="Segment distribution"), use_container_width=True)
metrics = [col for col in ["recency", "frequency", "monetary"] if col in segments]
if metrics:
    summary = segments.groupby("segment")[metrics].mean().reset_index()
    normalized = summary.copy()
    for metric in metrics:
        values = normalized[metric]
        normalized[metric] = (values - values.min()) / (values.max() - values.min()) if values.max() != values.min() else 0
    st.plotly_chart(px.bar(normalized, x="segment", y=metrics, barmode="group", range_y=[0, 1], title="Normalized RFM profile by segment"), use_container_width=True)
    st.caption("RFM axes are normalized independently to 0–1 so frequency and monetary values do not hide recency patterns. Segment labels are assigned from actual cluster mean profiles.")
st.dataframe(counts, use_container_width=True, hide_index=True)
st.download_button("Download segment summary CSV", counts.to_csv(index=False), "segment_summary.csv", "text/csv")
