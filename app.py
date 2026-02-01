import streamlit as st
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt

# ============================
# CORE IMPORTS (ROOT FILES)
# ============================
from sled_core import (
    SLEDEngine,
    safe_history,
    safe_news,
    apply_news_filter
)

from ledger_engine import (
    init_ledgers,
    log_signal,
    update_outcomes,
    update_attribution
)

# ============================
# STREAMLIT CONFIG
# ============================
st.set_page_config(
    page_title="SLEDAI — A7DO Manager",
    layout="wide",
    page_icon="🧿"
)

st.title("🧿 SLEDAI — A7DO MANAGER")
st.caption("Structure • Information • Constraint • Measurement")

# ============================
# STATE INITIALISATION
# ============================
init_ledgers(st.session_state)

if "sales_last_scan" not in st.session_state:
    st.session_state.sales_last_scan = []

if "inputs_log" not in st.session_state:
    st.session_state.inputs_log = []

# ============================
# ENGINE + UNIVERSE
# ============================
engine = SLEDEngine()

UNIVERSE = [
    "NVDA", "MSFT", "AAPL", "META", "AMZN",
    "TSLA", "AMD", "XOM", "JPM", "SPY"
]

# ============================
# MAIN CONTROL
# ============================
st.subheader("🚀 Autonomous Control")

if st.button("RUN FULL SLED CYCLE (A7DO)", type="primary"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.sales_last_scan = []

    for ticker in UNIVERSE:
        df = safe_history(ticker)
        if df is None:
            continue

        dfp = engine.calculate(df)
        if dfp is None:
            continue

        summary = engine.summarize(dfp)

        news = safe_news(ticker)
        final_action, reason = apply_news_filter(
            summary["Signal"], news
        )

        record = {
            "Timestamp": now,
            "Ticker": ticker,
            **summary,
            "Final_Action": final_action,
            "Reason": reason
        }

        st.session_state.sales_last_scan.append(record)

        # --- SIGNAL LEDGER (WRITE ONCE) ---
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

    # --- OUTCOMES + ATTRIBUTION ---
    update_outcomes(st.session_state)
    update_attribution(st.session_state)

    st.success("Cycle complete. Signals, outcomes, and attribution updated.")

st.divider()

# ============================
# RESULTS TABLE
# ============================
st.subheader("📈 Latest Market Decisions")

if st.session_state.sales_last_scan:
    st.dataframe(
        st.session_state.sales_last_scan,
        use_container_width=True
    )
else:
    st.info("No scan results yet. Run the cycle.")

st.divider()

# ============================
# COUPLING NETWORK (SIMPLE)
# ============================
st.subheader("🕸 Coupling Network (Decision Similarity)")

if st.session_state.sales_last_scan:
    G = nx.Graph()

    for r in st.session_state.sales_last_scan:
        G.add_node(
            r["Ticker"],
            action=r["Final_Action"]
        )

    # simple coupling: same action
    for i in range(len(st.session_state.sales_last_scan)):
        for j in range(i + 1, len(st.session_state.sales_last_scan)):
            a = st.session_state.sales_last_scan[i]
            b = st.session_state.sales_last_scan[j]
            if a["Final_Action"] == b["Final_Action"]:
                G.add_edge(a["Ticker"], b["Ticker"])

    pos = nx.spring_layout(G, seed=42)

    colors = []
    for n in G.nodes(data=True):
        if n[1]["action"] == "BUY":
            colors.append("green")
        elif n[1]["action"] == "SELL":
            colors.append("red")
        else:
            colors.append("lightgray")

    fig, ax = plt.subplots(figsize=(8, 6))
    nx.draw(
        G,
        pos,
        node_color=colors,
        with_labels=True,
        node_size=900,
        ax=ax
    )
    ax.set_title("BUY (green) • SELL (red) • WAIT (grey)")
    st.pyplot(fig)
else:
    st.info("Coupling network available after first run.")

st.divider()

# ============================
# LEDGER VIEWS
# ============================
st.subheader("🧾 Signal Ledger")
if not st.session_state.signal_ledger.empty:
    st.dataframe(
        st.session_state.signal_ledger.tail(20),
        use_container_width=True
    )
else:
    st.info("Signal ledger empty.")

st.subheader("📊 Attribution Ledger")
if not st.session_state.attribution_ledger.empty:
    st.dataframe(
        st.session_state.attribution_ledger.tail(20),
        use_container_width=True
    )

    accuracy = (
        st.session_state.attribution_ledger
        .Decision_Quality.eq("CORRECT")
        .mean() * 100
    )
    st.metric("Decision Accuracy (%)", round(accuracy, 2))
else:
    st.info("Attribution ledger empty.")

st.divider()

# ============================
# NAVIGATION
# ============================
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