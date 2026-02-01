import streamlit as st

st.set_page_config(page_title="Accounts", layout="wide")
st.title("💰 Accounts — Portfolio & Performance")

sig = st.session_state.get("signal_ledger")
att = st.session_state.get("attribution_ledger")

if sig is not None and not sig.empty:
    st.subheader("Signals")
    st.dataframe(sig.tail(20), use_container_width=True)
else:
    st.info("No signals yet.")

if att is not None and not att.empty:
    st.subheader("Attribution (Performance)")
    st.dataframe(att.tail(20), use_container_width=True)

    correct = (att.Decision_Quality=="CORRECT").mean()*100
    st.metric("Decision Accuracy (%)", round(correct,2))
else:
    st.info("No attribution data yet.")