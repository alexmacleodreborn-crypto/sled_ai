import streamlit as st
from datetime import datetime
import uuid

st.set_page_config(page_title="Doorman", layout="wide")
st.title("🚪 Doorman — Intake Control")

if "inputs_log" not in st.session_state:
    st.session_state.inputs_log = []

text = st.text_area("Incoming Input (text)", height=200)

if st.button("PROCESS INPUT"):
    tx = f"TX-{uuid.uuid4().hex[:10].upper()}"
    entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Transaction_Code": tx,
        "Type": "TEXT",
        "Content": text[:300],
        "Status": "ADMITTED"
    }
    st.session_state.inputs_log.insert(0, entry)
    st.success(f"Input admitted. Transaction code: {tx}")

st.subheader("Recent Inputs")
st.dataframe(st.session_state.inputs_log[:20], use_container_width=True)