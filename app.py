import streamlit as st
from datetime import datetime
import pandas as pd

from sled_core import SLEDEngine, safe_history
from transaction_engine import admit_transaction

# ==================================================
# STREAMLIT CONFIG
# ==================================================
st.set_page_config(
    page_title="SLEDAI — Auto Scan",
    layout="wide",
    page_icon="🧿",
)

st.title("🧿 SLEDAI — Autonomous Market Scan")
st.caption("Scan → Doorman → Downstream Processing")

# ==================================================
# STATE
# ==================================================
if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

engine = SLEDEngine()

# ==================================================
# STOCK UNIVERSE (100 CAN GO HERE)
# ==================================================
UNIVERSE = [
    "NVDA","MSFT","AAPL","META","AMZN","GOOGL","AMD","INTC","TSM","ASML",
    "ARM","TSLA","PLTR","COIN","SNOW","RIVN","XOM","CVX","OXY","SLB",
    "JPM","GS","BAC","MS","SPY","QQQ","IWM","XLF","XLE","JNJ","PG","KO",
    "PEP","WMT","COST","ORCL","IBM","CRM","ADBE","AVGO","QCOM","TXN",
    "AMAT","LRCX","MU","PANW","CRWD","NOW","SHOP","SQ","PYPL","ABNB",
    "DIS","NFLX","INTU","UBER","LYFT","BA","GE","CAT","DE","MMM",
    "NKE","SBUX","MCD","T","VZ","CSCO","ACN","SAP","SONY","TM",
    "BABA","JD","PDD","TSM","INFY","HDB","RIO","BHP","VALE"
]

# ==================================================
# RUN SCAN
# ==================================================
if st.button("🚀 RUN 7-DAY MARKET SCAN", type="primary"):

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    for ticker in UNIVERSE:

        df = safe_history(ticker)
        if df is None or len(df) < 7:
            continue

        # ---------------- PAST 7 DAYS ----------------
        past_7 = df["Close"].iloc[-7:]
        past_change = (past_7.iloc[-1] - past_7.iloc[0]) / past_7.iloc[0]

        # ---------------- SLED PROJECTION ----------------
        dfp = engine.calculate(df)
        summary = engine.summarize(dfp)

        # ---------------- BUILD ROW (ARRIVAL) ----------------
        row_text = (
            f"{ticker} auto scan | "
            f"Price={summary['Price']} | "
            f"Past7d={round(past_change*100,2)}% | "
            f"SLED={summary['Signal']} | "
            f"Gate={summary['Gate']} | "
            f"Z={summary['Z_Trap']} | "
            f"Sigma={summary['Sigma']} | "
            f"Forecast7d={summary['RiseScore_14d']}"
        )

        # ---------------- DOORMAN ONLY ----------------
        tx = admit_transaction(
            source="AUTO_SCAN",
            raw_text=row_text
        )

        st.session_state.transaction_ledger.insert(0, tx)

        results.append({
            "Ticker": ticker,
            "Price": summary["Price"],
            "Past_7d_%": round(past_change*100, 2),
            "SLED_Signal": summary["Signal"],
            "Gate": summary["Gate"],
            "Z_Trap": summary["Z_Trap"],
            "Sigma": summary["Sigma"],
            "Forecast_7d": summary["RiseScore_14d"],
            "TX_ID": tx["Transaction_ID"],
            "Accepted": tx["Accepted"],
        })

    st.success(f"Scan complete — {len(results)} arrivals sent to Doorman")

    st.subheader("📊 Scan Output (Arrivals)")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

# ==================================================
# LEDGER VIEW
# ==================================================
st.subheader("📜 Doorman Transaction Ledger (Latest 25)")
st.dataframe(
    st.session_state.transaction_ledger[:25],
    use_container_width=True
)