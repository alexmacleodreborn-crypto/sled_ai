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
        "Ticker": ticker,
        "Transactions_In_House": len(room.get("Transactions", [])),
        "Last_Updated": room.get("Last_Updated"),
        "Avg_Signal_Quality": room.get("Avg_Signal_Quality", 0.0),
    })

st.dataframe(guest_table, use_container_width=True)

# ==================================================
# RUN NEWS ON GUESTS
# ==================================================
st.divider()
st.subheader("📰 Run News on In-House Guests")

st.warning(
    "This will fetch recent business news for each guest and "
    "send results through Doorman as new arrivals."
)

if st.button("🔍 RUN NEWS CHECK", type="primary"):

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    news_count = 0

    for ticker in rooms.keys():

        profile = build_news_profile(ticker)

        if profile["News_Count"] == 0:
            continue

        # Build a structured, quantifiable news summary
        news_text = (
            f"{ticker} news update | "
            f"Sentiment={profile['Sentiment']} | "
            f"Articles={profile['News_Count']} | "
            f"NarrativePressure={profile['Narrative_Pressure']}"
        )

        tx = admit_transaction(
            source="NEWS",
            raw_text=news_text
        )

        st.session_state.transaction_ledger.insert(0, tx)
        news_count += 1

    st.success(f"News check complete — {news_count} news arrivals sent to Doorman")

# ==================================================
# LEDGER PREVIEW
# ==================================================
st.divider()
st.subheader("📜 Latest Concierge Transactions")

st.dataframe(
    st.session_state.transaction_ledger[:20],
    use_container_width=True
)