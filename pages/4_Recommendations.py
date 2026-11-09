import pandas as pd
import streamlit as st

from utils.calculations import product_label
from utils.data_loader import load_dashboard_data

st.title("Personalized Recommendations")
st.caption("ALS recommendations for known visitors, with popularity fallback for cold-start users.")
data = load_dashboard_data()
recs = data.recommendations
metadata = data.metadata
if recs.empty:
    st.warning("Recommendation exports are unavailable. Add ALS output to `data/recommendations`.")
    st.stop()
user_col = "user_id" if "user_id" in recs else next((c for c in recs if "user" in c.lower()), None)
product_col = "product_id" if "product_id" in recs else next((c for c in recs if "product" in c.lower() or "item" in c.lower()), None)
if not user_col or not product_col:
    st.error("The recommendation export needs identifiable user and product columns. Available columns: " + ", ".join(recs.columns))
    st.stop()
user_id = st.text_input("Search visitor ID", placeholder="Enter any visitor ID").strip()
limit = st.slider("Recommendations to show", 1, 20, 5)
known = recs[recs[user_col].astype(str).eq(user_id)] if user_id else pd.DataFrame()
source = "ALS Personalized" if not known.empty else "Popularity Fallback"
result = known.head(limit) if not known.empty else data.popularity.head(limit)
if user_id and known.empty:
    st.info("This visitor is not present in the ALS export. Showing the most-purchased products from the exported event data.")
st.caption(f"Recommendation source: **{source}**")
st.info("Precision@10 and Recall@10 exports were not present in `ecommerce_exports.zip`; no evaluation values are fabricated.")
if not result.empty and product_col in result:
    result = result.rename(columns={product_col: "product_id"})
    if "product_id" in metadata:
        result = result.merge(metadata.drop_duplicates("product_id"), on="product_id", how="left")
    result["Product"] = result.apply(product_label, axis=1)
    st.dataframe(result, use_container_width=True, hide_index=True)
    st.download_button("Download recommendations CSV", result.to_csv(index=False), "recommendations.csv", "text/csv")

if not data.evaluation.empty:
    st.markdown("### Recommendation evaluation")
    st.dataframe(data.evaluation, use_container_width=True, hide_index=True)
else:
    st.caption("No Precision@10 or Recall@10 export was found. Evaluation metrics are not available in the supplied project data.")
