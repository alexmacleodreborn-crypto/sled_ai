import streamlit as st
from transaction_engine import admit_transaction

st.set_page_config(page_title="Doorman", layout="wide")
st.title("🚪 Doorman — Controlled Intake")

if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

text = st.text_area("Incoming Information", height=200)

source = st.selectbox(
    "Source",
    ["NEWS","SALES_SCAN","MANUAL","FILE"]
)

if st.button("PROCESS"):
    tx = admit_transaction(source, text)
    st.session_state.transaction_ledger.insert(0, tx)

    if tx["Accepted"]:
        st.success(
            f"Accepted | Quality={tx['Signal_Quality']} | {tx['Transaction_ID']}"
        )
    else:
        st.error(
            f"Rejected | Quality={tx['Signal_Quality']} | Noise filtered"
        )

st.subheader("📜 Transaction Ledger (Latest)")
st.dataframe(
    st.session_state.transaction_ledger[:25],
    use_container_width=True
)