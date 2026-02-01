import streamlit as st
from datetime import datetime

from news_engine import build_news_profile
from transaction_engine import admit_transaction
from reception_engine import init_rooms

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Concierge",
    layout="wide",
)

st.title("🛎️ Concierge — Guest Intelligence Desk")
st.caption("Follow-up information only. No scanning. No decisions.")

# ==================================================
# STATE
# ==================================================
if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

init_rooms(st.session_state)
rooms = st.session_state.rooms

# ==================================================
# DISPLAY CURRENT GUESTS
# ==================================================
st.subheader("🏨 Guests Currently In-House")

if not rooms:
    st.info("No guests in-house yet. Run Auto Scan first.")
    st.stop()

guest_table = []
for ticker, room in rooms.items():
    guest_table.append({
        "Ticker":