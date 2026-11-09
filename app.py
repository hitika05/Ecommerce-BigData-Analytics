import streamlit as st

from utils.calculations import format_currency, format_number
from utils.data_loader import load_dashboard_data
from utils.visualizations import apply_plotly_theme

st.set_page_config(
    page_title="E-Commerce Big Data Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: #14213d; }
        .stApp { background: #f7f9fc; }
        [data-testid="stSidebar"] { background: #101b3a; }
        [data-testid="stSidebar"] * { color: #eef2ff !important; }
        .hero { background: linear-gradient(120deg, #14213d, #352c75); padding: 2.4rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; }
        .hero h1 { color: white; margin: 0 0 .45rem; font-size: 2.5rem; }
        .hero p { color: #dce5ff; margin: 0; font-size: 1.08rem; }
        .kpi { background: white; border: 1px solid #e8ecf4; border-radius: 14px; padding: 1rem 1.1rem; box-shadow: 0 4px 16px rgba(20,33,61,.05); }
        .kpi-label { color: #667085; font-size: .82rem; font-weight: 600; }
        .kpi-value { color: #14213d; font-family: 'Space Grotesk'; font-size: 1.55rem; font-weight: 700; margin-top: .25rem; }
        .section-note { color: #667085; font-size: .9rem; }
        .stDownloadButton button { border-color: #6750a4; color: #6750a4; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
apply_plotly_theme()
data = load_dashboard_data()

with st.sidebar:
    st.markdown("## ECOMMERCE\n### ANALYTICS")
    st.caption("Big Data Intelligence Platform")
    st.divider()
    st.markdown("### Data controls")
    st.caption(f"Price unit: {data.currency_label}")
    st.divider()
    st.markdown("### Project architecture")
    st.caption("Raw events → PySpark ETL → Parquet exports → Streamlit analytics")
    st.caption("Place exported folders under `data/` and refresh the app.")

st.markdown(
    '<div class="hero"><h1>E-Commerce Big Data Analytics</h1>'
    '<p>Transforming millions of customer interactions into actionable business intelligence.</p></div>',
    unsafe_allow_html=True,
)

if not data.has_any_data:
    st.info("No project exports were found yet. Add Parquet or CSV outputs to `data/analytics`, `data/recommendations`, `data/segments`, or `data/metadata`. Enable “sample preview” in the sidebar only to preview the UI.")

st.markdown("## Welcome to your analytics command center")
st.markdown("Use the navigation pages to explore customer behavior, product performance, recommendations, monitoring, and business decisions.")

metrics = data.overview_metrics()
cols = st.columns(4)
for col, (label, value) in zip(cols, [
    ("Events", format_number(metrics["events"])),
    ("Unique users", format_number(metrics["users"])),
    ("Purchases", format_number(metrics["purchases"])),
    ("Revenue", format_currency(metrics["revenue"], data.currency_label)),
]):
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("### What this project delivers")
left, right = st.columns(2)
with left:
    st.markdown("#### Trusted analytics")
    st.write("The dashboard reads processed PySpark outputs rather than loading the 5.28 GB source CSV. Schema inspection and column aliases keep exports flexible.")
    st.markdown("#### Customer intelligence")
    st.write("RFM segmentation and ALS recommendations are surfaced with product metadata, fallback handling, and exportable result tables.")
with right:
    st.markdown("#### Interactive decision support")
    st.write("Filter dates, categories, brands, and event types. Hover over Plotly charts for context and download the tables behind each view.")
    st.markdown("#### Deployment ready")
    st.write("Run locally with Streamlit, point the data directory at your copied Parquet folders, and keep historical replay monitoring clearly labeled.")

st.markdown("### Data readiness")
for name, ready in data.readiness().items():
    st.write(("✅" if ready else "⚪") + f" **{name}**")
