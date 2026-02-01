import streamlit as st
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt

from sled_core import (
    SLEDEngine,
    safe_history,
    safe_news,
    apply_news_filter,
)

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
st.caption("Structure → Information → Constraint → Measurement → Warp → Genesis")

# ==================================================
# STATE INITIALISATION
# ==================================================
init_ledgers(st.session_state)

if "sales_last_scan" not in st.session_state:
    st.session_state.sales_last_scan = []

if "inputs_log" not in st.session_state:
    st.session_state.inputs_log = []

engine = SLEDEngine()

UNIVERSE = [
    "NVDA", "MSFT", "AAPL", "META", "AMZN",
    "TSLA", "AMD", "XOM", "JPM", "SPY",
]

# ==================================================
# MAIN CONTROL
# ==================================================
st.subheader("🚀 Autonomous Control")

if st.button("RUN FULL SLED + WARP CYCLE (A7DO)", type="primary"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.sales_last_scan = []

    for ticker in UNIVERSE:
        df = safe_history(ticker)
        if df is None:
            continue

        dfp = engine.calculate(df)
        summary = engine.summarize(dfp)

        news = safe_news(ticker)
        final_action, reason = apply_news_filter(summary["Signal"], news)

        record = {
            "Timestamp": now,
            "Ticker": ticker,
            **summary,
            "Final_Action": final_action,
            "Reason": reason,
        }
        st.session_state.sales_last_scan.append(record)

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
                "Decision_Reason": reason,
            },
        )

    update_outcomes(st.session_state)
    update_attribution(st.session_state)
    update_warp_states(st.session_state)

    st.success("Cycle complete — SLED, Warp, Genesis ready.")

st.divider()

# ==================================================
# LATEST DECISIONS
# ==================================================
st.subheader("📈 Latest Market Decisions")
st.dataframe(st.session_state.sales_last_scan, use_container_width=True)

# ==================================================
# WHY WAIT
# ==================================================
st.subheader("🧠 WHY WAIT? — Structural Diagnostics")

wait_rows = []
for r in st.session_state.sales_last_scan:
    if r["Final_Action"] == "WAIT":
        regime = "STABLE"
        if r["Z_Trap"] > 0.85 and r["Gate"] < 1.0:
            regime = "OVER-COMPRESSED"
        elif r["Gate"] > 1.2 and r["Sigma"] < 1.0:
            regime = "LOW-FLOW"
        elif r["Gate"] < 0.8:
            regime = "ENERGY-EXHAUSTED"

        wait_rows.append({
            "Ticker": r["Ticker"],
            "Gate": r["Gate"],
            "Z_Trap": r["Z_Trap"],
            "Sigma": r["Sigma"],
            "Regime": regime,
        })

st.dataframe(wait_rows, use_container_width=True)

# ==================================================
# TIME-TO-WARP ESTIMATOR (NEW)
# ==================================================
st.subheader("⏳ Time-to-Warp Estimator")

ttw_rows = []
for r in st.session_state.sales_last_scan:
    readiness = (
        (r["Gate"] / 2.0) * 0.5 +
        (1 - r["Z_Trap"]) * 0.3 +
        (r["Sigma"] / 2.0) * 0.2
    )
    readiness = max(0, min(1, readiness))
    days = round((1 - readiness) * 10, 2)

    ttw_rows.append({
        "Ticker": r["Ticker"],
        "Warp_Readiness": round(readiness, 3),
        "Est_Days_to_Warp": days,
    })

st.dataframe(ttw_rows, use_container_width=True)

# ==================================================
# GENESIS DETECTOR (NEW)
# ==================================================
st.subheader("🌱 Genesis — Pre-Warp Precursors")

genesis = []
for r in st.session_state.sales_last_scan:
    if (
        r["Final_Action"] == "WAIT"
        and r["Z_Trap"] > 0.80
        and 0.9 < r["Gate"] < 1.3
        and r["Sigma"] < 1.2
    ):
        genesis.append({
            "Ticker": r["Ticker"],
            "Gate": r["Gate"],
            "Z_Trap": r["Z_Trap"],
            "Sigma": r["Sigma"],
            "Status": "GENESIS"
        })

if genesis:
    st.dataframe(genesis, use_container_width=True)
else:
    st.info("No Genesis configurations detected.")

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