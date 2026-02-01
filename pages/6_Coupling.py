import streamlit as st
from reception_engine import init_rooms
from coupling_engine import update_couplings

st.set_page_config(page_title="Coupling", layout="wide")
st.title("🔗 Coupling — Reinforcement Map")

# Initialise rooms (safe if already initialised)
init_rooms(st.session_state)

# Update couplings every page load
update_couplings(st.session_state)

rooms = st.session_state.get("rooms", {})

if not rooms:
    st.info("No rooms available yet. Add accepted transactions via Doorman.")
else:
    summary = []
    for r in rooms.values():
        c = r.get("Coupling", {})
        summary.append({
            "Ticker": r["Ticker"],
            "Internal_Coupling": c.get("Internal_Score", 0.0),
            "External_Coupling": c.get("External_Score", 0.0),
            "Total_Coupling": c.get("Total_Coupling", 0.0),
            "Coupling_State": c.get("Coupling_State", "WEAK"),
            "Transactions": len(r["Transactions"]),
        })

    st.subheader("📊 Coupling Summary")
    st.dataframe(summary, use_container_width=True)

st.divider()

# --------------------------------------------------
# ROOM-LEVEL DETAIL
# --------------------------------------------------
st.subheader("🔍 Room Coupling Detail")

ticker = st.selectbox(
    "Select Room",
    options=[""] + sorted(rooms.keys())
)

if ticker:
    room = rooms[ticker]
    st.markdown(f"### 🏨 Room: {ticker}")

    st.write("**Coupling Metrics**")
    st.json(room.get("Coupling", {}))

    st.write("**Event Counts**")
    st.json(dict(room.get("Event_Counts", {})))

    st.write("**Transactions**")
    st.dataframe(
        room.get("Transactions", []),
        use_container_width=True
    )