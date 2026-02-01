import streamlit as st

st.set_page_config(page_title="Reception", layout="wide")
st.title("🏨 Reception — Rooms In-House")

rooms = {}
for r in st.session_state.get("signal_ledger", []).to_dict("records"):
    t = r["Ticker"]
    rooms[t] = {
        "Ticker": t,
        "Final_Action": r["Final_Action"],
        "Gate": r["Gate"],
        "Z_Trap": r["Z_Trap"],
        "Timestamp": r["Timestamp"]
    }

if rooms:
    st.dataframe(list(rooms.values()), use_container_width=True)
else:
    st.info("No rooms allocated yet. Run a cycle.")