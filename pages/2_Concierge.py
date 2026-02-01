import streamlit as st
import pandas as pd

from reception_engine import init_rooms
from transaction_engine import admit_transaction
from news_engine import fetch_news_for_guest

st.set_page_config(page_title="Concierge", layout="wide")

st.title("🛎️ Concierge — Targeted Guest Intelligence")
st.caption("Select a guest and intent. Acquire only useful information.")

# --------------------------------------------------
# KEYWORD ENGINE
# --------------------------------------------------
KEYWORD_PROFILES = {
    "EARNINGS": [
        "earnings", "revenue", "profit", "guidance", "forecast"
    ],
    "GROWTH & CAPEX": [
        "investment", "capex", "expansion", "factory", "data center"
    ],
    "TECH / AI": [
        "artificial intelligence", "AI", "chips", "semiconductor", "cloud"
    ],
    "RISK & LEGAL": [
        "lawsuit", "investigation", "regulation", "fine", "ban"
    ],
    "M&A": [
        "acquisition", "merger", "buyout", "stake", "sale"
    ],
}

# --------------------------------------------------
# STATE
# --------------------------------------------------
init_rooms(st.session_state)
rooms = st.session_state.rooms

if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

if not rooms:
    st.info("No guests in-house yet. Run Auto Scan first.")
    st.stop()

# --------------------------------------------------
# SELECT GUEST
# --------------------------------------------------
st.subheader("🏨 Select Guest (Room)")

ticker = st.selectbox(
    "Choose in-house guest",
    options=sorted(rooms.keys())
)

room = rooms[ticker]

st.write(f"**Guest:** {ticker}")
st.write(f"**Check-ins:** {len(room.get('History', []))}")
st.write(f"**Avg Signal Quality:** {room.get('Avg_Signal_Quality', 0.0)}")

# --------------------------------------------------
# SELECT INTENT
# --------------------------------------------------
st.divider()
st.subheader("🎯 Select Information Intent")

intent = st.selectbox(
    "What are we looking for?",
    options=list(KEYWORD_PROFILES.keys())
)

keywords = KEYWORD_PROFILES[intent]

st.write("**Search Keywords:**")
st.code(", ".join(keywords))

# --------------------------------------------------
# RUN TARGETED NEWS
# --------------------------------------------------
st.divider()

if st.button("🔍 RUN TARGETED NEWS SEARCH", type="primary"):

    articles = fetch_news_for_guest(ticker)

    count = 0

    for art in articles:
        text = f"{art['Title']} {art.get('Raw_Text','')}".lower()

        if not any(k.lower() in text for k in keywords):
            continue

        keyword_tags = [f"TOPIC:{intent.replace(' ', '_')}"]

        raw_text = (
            f"{art['Company']} ({ticker}) news | "
            f"{intent} | "
            f"{art['Title']}"
        )

        tx = admit_transaction(
            source="NEWS",
            raw_text=raw_text
        )

        # Manually enrich tags
        tx["Tags"].extend(keyword_tags)

        st.session_state.transaction_ledger.insert(0, tx)
        count += 1

    st.success(f"{count} targeted news items admitted via Doorman")

# --------------------------------------------------
# PREVIEW LATEST NEWS
# --------------------------------------------------
st.divider()
st.subheader("📜 Latest News Arrivals")

st.dataframe(
    st.session_state.transaction_ledger[:20],
    use_container_width=True
)