import streamlit as st
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt

# ==================================================
# CORE IMPORTS
# ==================================================
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
st.caption("Structure → Information → Constraint → Measurement → Warp")

# ==================================================
# STATE INITIALISATION
# ==================================================
init_ledgers(st.session_state)

if "sales_last_scan" not in st.session_state:
    st.session_state.sales_last_scan = []

if "inputs_log" not in st.session_state:
    st.session_state.inputs_log = []

# ==================================================
# ENGINE + UNIVERSE
# ==================================================
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
            "Reason": reason,
        }

        st.session_state.sales_last_scan.append(record)

        # ---------------- SIGNAL LEDGER ----------------
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

    # ---------------- OUTCOME → ATTRIBUTION → WARP ----------------
    update_outcomes(st.session_state)
    update_attribution(st.session_state)
    update_warp_states(st.session_state)

    st.success("Cycle complete — SLED, Ledger, and Warp updated.")

st.divider()

# ==================================================
# LATEST DECISIONS
# ==================================================
st.subheader("📈 Latest Market Decisions")

if st.session_state.sales_last_scan:
    st.dataframe(
        st.session_state.sales_last_scan,
        use_container_width=True,
    )
else:
    st.info("No scan results yet. Run the cycle.")

st.divider()

# ==================================================
# WARP SUMMARY PANEL
# ==================================================
st.subheader("🌀 Warp State Summary")

if (
    hasattr(st.session_state, "attribution_ledger")
    and not st.session_state.attribution_ledger.empty
    and "Warp_State" in st.session_state.attribution_ledger.columns
):
    warp_counts = (
        st.session_state.attribution_ledger["Warp_State"]
        .value_counts()
        .rename_axis("Warp_State")
        .reset_index(name="Count")
    )
    st.dataframe(warp_counts, use_container_width=True)
else:
    st.info("Warp states will appear after outcomes are evaluated.")

st.divider()

# ==================================================
# COUPLING NETWORK (WARP-AWARE)
# ==================================================
st.subheader("🕸 Coupling Network (Final Action + Warp)")

if st.session_state.sales_last_scan:
    G = nx.Graph()

    # build lookup for warp
    warp_lookup = {}
    if not st.session_state.attribution_ledger.empty:
        for _, r in st.session_state.attribution_ledger.iterrows():
            warp_lookup[r["Ticker"]] = r.get("Warp_State", "")

    # add nodes
    for r in st.session_state.sales_last_scan:
        G.add_node(
            r["Ticker"],
            action=r["Final_Action"],
            warp=warp_lookup.get(r["Ticker"], ""),
        )

    # simple coupling: same final action
    rows = st.session_state.sales_last_scan
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if rows[i]["Final_Action"] == rows[j]["Final_Action"]:
                G.add_edge(rows[i]["Ticker"], rows[j]["Ticker"])

    pos = nx.spring_layout(G, seed=42)

    colors = []
    for _, data in G.nodes(data=True):
        if data["warp"] == "WARP_UP":
            colors.append("lime")
        elif data["warp"] == "WARP_DOWN":
            colors.append("red")
        elif data["action"] == "BUY":
            colors.append("green")
        elif data["action"] == "SELL":
            colors.append("darkred")
        else:
            colors.append("lightgray")

    fig, ax = plt.subplots(figsize=(9, 6))
    nx.draw(
        G,
        pos,
        node_color=colors,
        with_labels=True,
        node_size=900,
        ax=ax,
    )
    ax.set_title(
        "Warp-Aware Coupling\n"
        "Lime = WARP_UP • Red = WARP_DOWN • Grey = POST/PRE",
        fontsize=11,
    )
    st.pyplot(fig)
else:
    st.info("Coupling network available after first run.")

st.divider()

# ==================================================
# LEDGER VIEWS
# ==================================================
st.subheader("🧾 Signal Ledger")
if not st.session_state.signal_ledger.empty:
    st.dataframe(
        st.session_state.signal_ledger.tail(20),
        use_container_width=True,
    )
else:
    st.info("Signal ledger empty.")

st.subheader("📊 Attribution + Warp Ledger")
if not st.session_state.attribution_ledger.empty:
    st.dataframe(
        st.session_state.attribution_ledger.tail(20),
        use_container_width=True,
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