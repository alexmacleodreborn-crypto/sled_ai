import streamlit as st
from reception_engine import init_rooms, check_in_transaction

st.set_page_config(page_title="Reception", layout="wide")
st.title("🏨 Reception — Rooms In House")

# Initialise rooms
init_rooms(st.session_state)

ledger = st.session_state.get("transaction_ledger", [])

# Check in any new accepted transactions
for tx in ledger:
    check_in_transaction(st.session_state, tx)

# Display rooms
rooms = st.session_state.rooms

if not rooms:
    st.info("No rooms yet. Accepted transactions will appear here.")
else:
    display = []
    for r in rooms.values():
        display.append({
            "Ticker": r["Ticker"],
            "Transactions": len(r["Transactions"]),
            "Avg_Signal_Quality": r["Avg_Signal_Quality"],
            "Last_Event": r["Last_Event"],
            "Last_Updated": r["Last_Updated"],
        })

    st.dataframe(display, use_container_width=True)

# Drill-down
st.subheader("🔍 Room Details")

ticker = st.selectbox(
    "Select Ticker Room",
    options=[""] + sorted(rooms.keys())
)

if ticker:
    room = rooms[ticker]
    st.markdown(f"### Room: {ticker}")
    st.write("**Event Counts**", dict(room["Event_Counts"]))
    st.dataframe(room["Transactions"], use_container_width=True)