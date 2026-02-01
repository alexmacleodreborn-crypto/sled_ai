import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doorman", layout="wide")

st.title("🚪 Doorman — Arrival Control & Transaction Codes")
st.caption("Passive intake only. No scanning. No analysis.")

# --------------------------------------------------
# STATE
# --------------------------------------------------
ledger = st.session_state.get("transaction_ledger", [])

if not ledger:
    st.info("No arrivals yet. Run Auto Scan or Concierge News.")
    st.stop()

# --------------------------------------------------
# SUMMARY METRICS
# --------------------------------------------------
accepted = sum(1 for t in ledger if t.get("Accepted"))
rejected = len(ledger) - accepted

c1, c2, c3 = st.columns(3)
c1.metric("Total Arrivals", len(ledger))
c2.metric("Accepted", accepted)
c3.metric("Rejected", rejected)

# --------------------------------------------------
# TABLE VIEW
# --------------------------------------------------
st.subheader("📜 Arrival Log")

df = pd.DataFrame(ledger)

display_cols = [
    "Transaction_ID",
    "Timestamp",
    "Source",
    "Ticker",
    "Signal_Quality",
    "Accepted",
    "Tags",
    "Raw_Text",
]

st.dataframe(
    df[display_cols],
    use_container_width=True,
    height=500
)

# --------------------------------------------------
# FILTERS
# --------------------------------------------------
st.subheader("🔎 Filters")

f1, f2 = st.columns(2)

with f1:
    source_filter = st.multiselect(
        "Filter by Source",
        options=sorted(df["Source"].unique()),
        default=sorted(df["Source"].unique())
    )

with f2:
    ticker_filter = st.multiselect(
        "Filter by Ticker",
        options=sorted(df["Ticker"].dropna().unique()),
        default=sorted(df["Ticker"].dropna().unique())
    )

filtered = df[
    df["Source"].isin(source_filter)
    & df["Ticker"].isin(ticker_filter)
]

st.subheader("📂 Filtered Arrivals")
st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    height=400
)