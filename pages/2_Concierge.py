import streamlit as st
import pandas as pd
from datetime import datetime

from reception_engine import init_rooms
from news_engine import fetch_news_for_guest
from transaction_engine import admit_transaction

st.set_page_config(page_title="Concierge", layout="wide")

st.title("🛎️ Concierge — Guest Intelligence Follow-Up")
st.caption("News follow-ups only. No scanning. No decisions.")

# --------------------------------------------------
# STATE
# --------------------------------------------------
init_rooms(st.session_state)
rooms = st.session_state.rooms

if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

# --------------------------------------------------
# GUEST LIST
# --------------------------------------------------
st.subheader("🏨 Guests Currently In-House")

if not rooms:
    st.info("No guests in-house yet. Run Auto Scan first.")
    st.stop()

guest_rows = []
for ticker, room in rooms.items():
    guest_rows.append({
        "Ticker": ticker,
        "Check-Ins": len(room.get("History", [])),
        "Transactions": len(room.get("Transactions", [])),
        "Avg_Signal_Quality": room.get("Avg_Signal_Quality", 0.0),
        "Last_CheckIn": room.get("Last_CheckIn"),
    })

st.dataframe(pd.DataFrame(guest_rows), use_container_width=True)

# --------------------------------------------------
# NEWS ACTION
# --------------------------------------------------
st.divider()
st.subheader("📰 Run News on Guests")

st.warning(
    "This fetches business news for each in-house guest and "
    "routes each item through Doorman as a new arrival."
)

if st.button("🔍 RUN NEWS CHECK", type="primary"):

    news_total = 0

    for ticker in rooms.keys():

        articles = fetch_news_for_guest(ticker)

        for art in articles:

            keyword_text = " ".join(art["Keywords"])

            raw_text = (
                f"{art['Company']} ({ticker}) news | "
                f"{keyword_text} | "
                f"{art['Title']}"
            )

            tx = admit_transaction(
                source="NEWS",
                raw_text=raw_text
            )

            st.session_state.transaction_ledger.insert(0, tx)
            news_total += 1

    st.success(f"{news_total} news items admitted via Doorman")

# --------------------------------------------------
# PREVIEW LATEST NEWS ARRIVALS
# --------------------------------------------------
st.divider()
st.subheader("📜 Latest News Arrivals")

st.dataframe(
    st.session_state.transaction_ledger[:25],
    use_container_width=True
)