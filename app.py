import streamlit as st
from datetime import datetime
import pandas as pd

from sled_core import (
    SLEDEngine,
    safe_history,
)

from news_engine import build_news_profile

from ledger_engine import (
    init_ledgers,
    log_signal,
    update_outcomes,
    update_attribution,
)

from warp_engine import update_warp_states


# ==================================================
# STREAMLIT CONFIG
# ==================================================
st.set_page_config(
    page_title="SLEDAI — A7DO Manager",
    layout="wide",
    page_icon="🧿",
)

st.title("🧿 SLEDAI — A7DO Manager")
st.caption("WAIT → PREPARE → BUY / SELL → WARP → GENESIS")

# ==================================================
# STATE INIT
# ==================================================
init_ledgers(st.session_state)

if "sales_last_scan" not in st.session_state:
    st.session_state.sales_last_scan = []

engine = SLEDEngine()

# ==================================================
# LARGE, DIVERSE UNIVERSE
# ==================================================
UNIVERSE = [
    "NVDA","MSFT","AAPL","META","AMZN","GOOGL",
    "AMD","INTC","TSM","ASML","ARM",
    "TSLA","PLTR","COIN","SNOW","RIVN",
    "XOM","CVX","OXY","SLB",
    "JPM","GS","BAC","MS",
    "SPY","QQQ","IWM","XLF","XLE",
    "JNJ","PG","KO","PEP","WMT",
]

# ==================================================
# RUN ENGINE
# ==================================================
if st.button("🚀 RUN FULL SLED + NEWS CYCLE", type="primary"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.sales_last_scan = []

    for ticker in UNIVERSE:
        df = safe_history(ticker)
        if df is None:
            continue

        dfp = engine.calculate(df)
        summary = engine.summarize(dfp)

        # ---------------- NEWS PROFILE ----------------
        news_profile = build_news_profile(ticker)

        # ---------------- ACTION LOGIC ----------------
        final_action = summary["Signal"]
        display_action = final_action

        if final_action == "WAIT" and summary["Prepare"]:
            if news_profile["Sentiment"] in ("POSITIVE", "MIXED"):
                display_action = "PREPARE"

        record = {
            "Timestamp": now,
            "Ticker": ticker,
            "Price": summary["Price"],
            "Action": display_action,
            "Gate": summary["Gate"],
            "Z_Trap": summary["Z_Trap"],
            "Sigma": summary["Sigma"],
            "RiseScore_14d": summary["RiseScore_14d"],
            "News_Sentiment": news_profile["Sentiment"],
            "Narrative_Pressure": news_profile["Narrative_Pressure"],
        }

        st.session_state.sales_last_scan.append(record)

        # ---------------- LEDGER ----------------
        log_signal(
            st.session_state,
            {
                "Timestamp": now,
                "Ticker": ticker,
                "Raw_Signal": summary["Signal"],
                "Final_Action": final_action,
                "Gate": summary["Gate"],
                "Z_Trap": summary["Z_Trap"],
                "Sigma": summary["Sigma"],
                "RiseScore_14d": summary["RiseScore_14d"],
                "Bullseye": summary["Bullseye"],
                "Narrative_Pressure": news_profile["Narrative_Pressure"],
            }
        )

    update_outcomes(st.session_state)
    update_attribution(st.session_state)
    update_warp_states(st.session_state)

    st.success("Cycle complete — SLED + News integrated")

# ==================================================
# OUTPUT — MARKET STATE
# ==================================================
st.subheader("📊 Market State")

df = pd.DataFrame(st.session_state.sales_last_scan)

if not df.empty:
    st.dataframe(df, use_container_width=True)

    st.subheader("Action Distribution")
    st.bar_chart(df["Action"].value_counts())

else:
    st.info("Run the cycle to populate results.")

# ==================================================
# NEWS PROFILES
# ==================================================
st.subheader("📰 Stock News Profiles")

profiles = []
for r in st.session_state.sales_last_scan:
    profiles.append({
        "Ticker": r["Ticker"],
        "News_Sentiment": r["News_Sentiment"],
        "Narrative_Pressure": r["Narrative_Pressure"],
    })

st.dataframe(profiles, use_container_width=True)

# ==================================================
# NAVIGATION
# ==================================================
st.subheader("🧭 Navigation")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    if st.button("🚪 Doorman"):
        st.switch_page("pages/1_Doorman.py")
with c2:
    if st.button("🛎 Concierge"):
        st.switch_page("pages/2_Concierge.py")
with c3:
    if st.button("🏨 Reception"):
        st.switch_page("pages/3_Reception.py")
with c4:
    if st.button("📈 Sales"):
        st.switch_page("pages/4_SalesMarketing.py")
with c5:
    if st.button("💰 Accounts"):
        st.switch_page("pages/5_Accounts.py")