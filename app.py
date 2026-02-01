import streamlit as st
from datetime import datetime
import pandas as pd

# ---------------- CORE ENGINES ----------------
from sled_core import SLEDEngine, safe_history
from news_engine import build_news_profile
from decision_engine import final_decision

# ---------------- GOVERNANCE ----------------
from transaction_engine import admit_scan_transaction
from reception_engine import init_rooms, check_in_transaction
from coupling_engine import update_couplings

from ledger_engine import init_ledgers, log_signal


# ==================================================
# STREAMLIT CONFIG
# ==================================================
st.set_page_config(
    page_title="SLEDAI — A7DO Manager",
    layout="wide",
    page_icon="🧿",
)

st.title("🧿 SLEDAI — A7DO Manager")
st.caption("All intelligence flows through Doorman → Rooms → Coupling → Decision")

# ==================================================
# INITIALISE GLOBAL STATE
# ==================================================
init_ledgers(st.session_state)
init_rooms(st.session_state)

if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

if "cycle_results" not in st.session_state:
    st.session_state.cycle_results = []

engine = SLEDEngine()

# ==================================================
# STOCK UNIVERSE
# ==================================================
UNIVERSE = [
    "NVDA","MSFT","AAPL","META","AMZN","GOOGL",
    "AMD","INTC","TSM","ASML","ARM",
    "TSLA","PLTR","COIN","SNOW","RIVN",
    "XOM","CVX","OXY","SLB",
    "JPM","GS","BAC","MS",
]

# ==================================================
# RUN FULL INTELLIGENCE CYCLE
# ==================================================
if st.button("🚀 RUN FULL GOVERNED INTELLIGENCE CYCLE", type="primary"):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.cycle_results = []

    # --- CLEAR ROOMS & REBUILD FROM LEDGER ---
    init_rooms(st.session_state)

    # --- MAIN LOOP ---
    for ticker in UNIVERSE:

        # ---------------- PRICE ----------------
        df = safe_history(ticker)
        if df is None:
            continue

        dfp = engine.calculate(df)
        summary = engine.summarize(dfp)

        # ---------------- NEWS ----------------
        news_profile = build_news_profile(ticker)

        # ---------------- DOORMAN INGESTION ----------------
        tx = admit_scan_transaction(
            ticker=ticker,
            sled_summary=summary,
            news_profile=news_profile
        )

        st.session_state.transaction_ledger.insert(0, tx)

        # ---------------- RECEPTION CHECK-IN ----------------
        check_in_transaction(st.session_state, tx)

    # ---------------- COUPLING UPDATE ----------------
    update_couplings(st.session_state)

    # ---------------- FINAL DECISION MATRIX ----------------
    for ticker, room in st.session_state.rooms.items():

        summary = next(
            (t for t in st.session_state.transaction_ledger
             if t["Ticker"] == ticker and t["Accepted"]),
            None
        )

        if not summary:
            continue

        news_profile = build_news_profile(ticker)
        coupling = room.get("Coupling", {})

        action, confidence, reasons = final_decision(
            sled_signal="WAIT",            # raw signal already encoded in tx
            prepare=True,                  # PREPARE emerges from SLED + room
            coupling=coupling,
            narrative_pressure=news_profile["Narrative_Pressure"],
        )

        record = {
            "Timestamp": now,
            "Ticker": ticker,
            "Final_Action": action,
            "Confidence": confidence,
            "Reasons": ", ".join(reasons),
            "Coupling": coupling.get("Coupling_State", "NONE"),
            "News": news_profile["Sentiment"],
            "Avg_Signal_Quality": room.get("Avg_Signal_Quality", 0.0),
            "Transactions": len(room.get("Transactions", [])),
        }

        st.session_state.cycle_results.append(record)

        log_signal(
            st.session_state,
            {
                "Timestamp": now,
                "Ticker": ticker,
                "Final_Action": action,
                "Confidence": confidence,
                "Reasons": reasons,
            }
        )

    st.success("Cycle complete — all data flowed through Doorman")

# ==================================================
# OUTPUT — FINAL MATRIX
# ==================================================
st.subheader("📊 Final Decision Matrix")

df = pd.DataFrame(st.session_state.cycle_results)

if not df.empty:
    st.dataframe(df, use_container_width=True)

    st.subheader("Action Distribution")
    st.bar_chart(df["Final_Action"].value_counts())
else:
    st.info("Run the cycle to generate decisions.")

# ==================================================
# GOVERNANCE VISIBILITY
# ==================================================
st.subheader("📜 Transaction Ledger (Latest 20)")
st.dataframe(
    st.session_state.transaction_ledger[:20],
    use_container_width=True
)