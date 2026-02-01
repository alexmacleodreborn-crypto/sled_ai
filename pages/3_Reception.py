import streamlit as st
from reception_engine import init_rooms, check_in_transaction

st.set_page_config(page_title="Reception", layout="wide")
st.title("🏨 Reception — In-House Continuity")

init_rooms(st.session_state)

ledger = st.session_state.get("transaction_ledger", [])

# --------------------------------------------------
# Check in new arrivals
# --------------------------------------------------
for tx in ledger:
    check_in_transaction(st.session_state, tx)

rooms = st.session_state.rooms

if not rooms:
    st.info("No guests checked in yet.")
    st.stop()

# --------------------------------------------------
# Summary table
# --------------------------------------------------
summary = []
for r in rooms.values():
    t = r.get("Transitions", {})
    summary.append({
        "Ticker": r["Ticker"],
        "Check-Ins": len(r["History"]),
        "Gate_Trend": t.get("Gate", "INIT"),
        "Sigma_Trend": t.get("Sigma", "INIT"),
        "Z_Trend": t.get("Z_Trap", "INIT"),
        "Avg_Signal_Quality": r["Avg_Signal_Quality"],
        "Last_CheckIn": r["Last_CheckIn"],
    })

st.subheader("📊 Guests In-House")
st.dataframe(summary, use_container_width=True)

# --------------------------------------------------
# Drill-down
# --------------------------------------------------
st.subheader("🔍 Guest History")

ticker = st.selectbox(
    "Select Guest",
    options=sorted(rooms.keys())
)

room = rooms[ticker]

st.markdown(f"### {ticker}")

st.write("**Transitions**")
st.json(room.get("Transitions", {}))

st.write("**History**")
st.dataframe(room.get("History", []), use_container_width=True)

st.write("**Transactions**")
st.dataframe(room.get("Transactions", []), use_container_width=True)