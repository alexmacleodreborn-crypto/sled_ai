import streamlit as st
from sled_core import safe_history, safe_news, apply_news_filter, SLEDEngine

st.set_page_config(page_title="Sales & Marketing", layout="wide")
st.title("📈 Sales & Marketing — Stock Intelligence")

engine = SLEDEngine()
ticker = st.text_input("Enter Ticker", "NVDA").upper()

if st.button("RUN REPORT"):
    df = safe_history(ticker)
    if df is None:
        st.error("No data available")
    else:
        dfp = engine.calculate(df)
        s = engine.summarize(dfp)
        news = safe_news(ticker)
        final, reason = apply_news_filter(s["Signal"], news)

        st.subheader(f"Report: {ticker}")
        st.json({**s,"Final_Action":final,"Reason":reason})

        if news:
            st.subheader("Relevant News")
            st.dataframe(news)