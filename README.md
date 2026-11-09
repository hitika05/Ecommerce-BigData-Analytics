# E-Commerce Big Data Analytics Dashboard

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Connected export package

The supplied `ecommerce_exports.zip` was extracted into `data/_imported/` and is already wired into the loader:

- `data/_imported/clean_events/`: 4,239,022 partitioned event rows.
- `data/_imported/recommendations/`: 2,066,645 ALS recommendation rows.
- `data/_imported/segments/`: 60,776 RFM/K-Means rows.

The event export contains `event_time`, `event_type`, `product_id`, `category_code`, `brand`, `price`, `user_id`, `hour`, and `main_category`. Product metadata is derived from these real event columns because the ZIP did not contain a separate metadata export. Product names were not present, so the UI uses brand/category as the primary product label and product ID as secondary information.

The ZIP did not include Precision@10 or Recall@10 result files. The Recommendations page reports those metrics as unavailable rather than fabricating values.

## Connect future Colab/PySpark exports

Copy processed exports into the matching folders:

- `data/analytics/`: event-level or pre-aggregated analytics containing columns such as `event_type`, `event_time`, `product_id`, `category`, `brand`, `price`, and `user_id`.
- `data/metadata/`: product metadata with a `product_id` plus available brand/category/price fields.
- `data/segments/`: RFM/K-Means results with `user_id`, `recency`, `frequency`, and `monetary`. An existing `segment` label is respected.
- `data/recommendations/`: ALS results with user/product identifiers and a score or prediction column.

Parquet files, partitioned Parquet folders, and CSV files are supported. The loader inspects schemas and aliases common column names; it does not fabricate business results. Set `st.secrets["DATA_ROOT"]` to use a different data directory.

The real-time page is explicitly a replay view when the exported data is historical. It does not claim to connect to a production streaming system.
