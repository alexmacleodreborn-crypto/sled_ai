import streamlit as st

st.set_page_config(page_title="Concierge", layout="wide")
st.title("🛎 Concierge — Classification")

inputs = st.session_state.get("inputs_log", [])

classified = []
for i in inputs:
    c = "INFO"
    txt = i.get("Content","").lower()
    if any(k in txt for k in ["buy","sell","earnings","guidance"]):
        c = "ACTION_REQUIRED"
    elif any(k in txt for k in ["wait","uncertain","hold"]):
        c = "WATCH"
    classified.append({**i,"Category":c})

st.dataframe(classified[:25], use_container_width=True)