import streamlit as st
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt

from sled_core import *
from ledger_engine import *

st.set_page_config("SLEDAI","wide","🧿")
st.title("🧿 SLEDAI — A7DO Manager")

init_ledgers(st.session_state)
engine = SLEDEngine()

UNIVERSE = ["NVDA","MSFT","AAPL","META","AMZN","TSLA","XOM","JPM","SPY"]

if st.button("RUN FULL CYCLE"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.sales_last_scan=[]

    for t in UNIVERSE:
        df = safe_history(t)
        if df is None: continue
        dfp = engine.calculate(df)
        s = engine.summarize(dfp)
        news = safe_news(t)
        final, reason = apply_news_filter(s["Signal"],news)

        row = {
            "Timestamp": now,
            "Ticker": t,
            **s,
            "Final_Action": final,
            "Reason": reason
        }
        st.session_state.sales_last_scan.append(row)
        log_signal(st.session_state,row)

    update_outcomes(st.session_state)
    update_attribution(st.session_state)

st.subheader("BUY / SELL / WAIT")
st.dataframe(st.session_state.sales_last_scan)

st.subheader("Signal Ledger")
st.dataframe(st.session_state.signal_ledger)

st.subheader("Attribution Ledger")
st.dataframe(st.session_state.attribution_ledger)