import streamlit as st
from datetime import datetime
import pandas as pd
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
st.caption("Structure → Constraint → Warp → Genesis → Validation")

# ==================================================
# STATE INITIALISATION
# ==================================================
init_ledgers(st.session_state)

if "sales_last_scan" not in st.session_state:
    st.session_state.sales_last_scan = []

if "genesis_log" not in st.session_state:
    st.session_state.genesis_log = pd.DataFrame(
        columns=["Timestamp", "Ticker"]
    )

engine = SLEDEngine()

# ==================================================
# EXPANDED UNIVERSE (DIVERSITY MATTERS)
# ==================================================
UNIVERSE = [
    # Mega-cap tech
    "NVDA","MSFT","AAPL","META","AMZN","GOOGL",
    # Semiconductors
    "AMD","INTC","TSM","ASML","ARM",
    # Growth / Volatile
    "TSLA","PLTR","COIN","RIVN","SNOW",
    # Energy
    "XOM","CVX","OXY","SLB",
    # Financials
    "JPM","GS","BAC","MS",
    # ETFs / Market
    "SPY","QQQ","IWM","XLF","XLE",
    # Defensive
    "JNJ","PG","KO","PEP","WMT",
]

# ==================================================
# MAIN CONTROL
# ==================================================
st.subheader("🚀 Autonomous Control")

if st.button("RUN FULL SLED + WARP + GENESIS CYCLE (A7DO)", type="primary"):
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
            }
        )

        # ---------------- GENESIS DETECTION (LOGGED) ----------------
        if (
            final_action == "WAIT"
            and summary["Z_Trap"] > 0.80
            and 0.9 < summary["Gate"] < 1.3
            and summary["Sigma"] < 1.2
        ):
            st.session_state.genesis_log = pd.concat(
                [
                    st.session_state.genesis_log,
                    pd.DataFrame([{
                        "Timestamp": now,
                        "Ticker": ticker
                    }])
                ],
                ignore_index=True
            )

    update_outcomes(st.session_state)
    update_attribution(st.session_state)
    update_warp_states(st.session_state)

    st.success("Cycle complete — Genesis logged, Warp evaluated.")

st.divider()

# ==================================================
# LATEST DECISIONS
# ==================================================
st.subheader("📈 Latest Market Decisions")
st.dataframe(st.session_state.sales_last_scan, use_container_width=True)

# ==================================================
# GENESIS VALIDATION (NEW, CRITICAL)
# ==================================================
st.subheader("🧪 Genesis Validation (Measured)")

if not st.session_state.genesis_log.empty and not st.session_state.attribution_ledger.empty:
    merged = pd.merge(
        st.session_state.genesis_log,
        st.session_state.attribution_ledger,
        on=["Timestamp","Ticker"],
        how="left"
    )

    total = len(merged)
    warp_up = (merged["Warp_State"] == "WARP_UP").sum()
    warp_down = (merged["Warp_State"] == "WARP_DOWN").sum()

    st.metric("Genesis Events", total)
    st.metric("Genesis → WARP_UP (%)", round(warp_up / max(1,total) * 100, 2))
    st.metric("Genesis → WARP_DOWN (%)", round(warp_down / max(1,total) * 100, 2))

    st.dataframe(
        merged[["Timestamp","Ticker","Warp_State","Decision_Quality"]],
        use_container_width=True
    )
else:
    st.info("Genesis validation will populate after multiple cycles.")

# ==================================================
# TIME-TO-WARP ESTIMATOR
# ==================================================
st.subheader("⏳ Time-to-Warp Estimator")

ttw = []
for r in st.session_state.sales_last_scan:
    readiness = (
        (r["Gate"] / 2.0) * 0.5 +
        (1 - r["Z_Trap"]) * 0.3 +
        (r["Sigma"] / 2.0) * 0.2
    )
    readiness = max(0, min(1, readiness))
    ttw.append({
        "Ticker": r["Ticker"],
        "Warp_Readiness": round(readiness, 3),
        "Est_Days_to_Warp": round((1 - readiness) * 10, 2)
    })

st.dataframe(ttw, use_container_width=True)

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