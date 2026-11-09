import plotly.express as px
import streamlit as st

from utils.data_loader import load_dashboard_data

st.title("Real-Time Monitoring")
st.caption("Simulated/replay monitoring of exported historical events; this is not production live traffic.")
data = load_dashboard_data()
events = data.analytics
if events.empty:
    st.warning("Historical event exports are unavailable.")
    st.stop()
running = st.toggle("Start replay simulation", value=False)
window_size = st.slider("Replay window size", 1000, min(len(events), 50000), min(10000, len(events)), step=1000)
if "replay_cursor" not in st.session_state:
    st.session_state.replay_cursor = window_size
if st.session_state.replay_cursor > len(events) or not running:
    st.session_state.replay_cursor = window_size
if running and st.button("Advance replay window"):
    st.session_state.replay_cursor = min(st.session_state.replay_cursor + window_size, len(events))
    st.rerun()
cursor = st.session_state.replay_cursor
latest = events.iloc[max(0, cursor - window_size):cursor]
st.caption(f"Replay window: rows {max(1, cursor - len(latest) + 1):,}–{cursor:,} of {len(events):,}. Toggle replay on and advance the window to update counters and charts.")
counts = latest["event_type"].astype(str).str.lower().value_counts()
for col, (label, value) in zip(st.columns(4), [("Events", len(latest)), ("Views", counts.get("view", 0)), ("Cart additions", counts.get("cart", 0)), ("Purchases", counts.get("purchase", 0))]):
    col.metric(label, f"{value:,}")
if "event_time" in latest:
    windows = latest.assign(window=latest["event_time"].dt.floor("H")).groupby(["window", "event_type"]).size().reset_index(name="events")
    st.plotly_chart(px.line(windows, x="window", y="events", color="event_type", markers=True, title="Events per replay time window"), use_container_width=True)
    st.plotly_chart(px.area(windows, x="window", y="events", color="event_type", title="Event distribution over time"), use_container_width=True)
