import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

from reception_engine import init_rooms
from sled_core import SLEDEngine, safe_history
from transaction_engine import admit_transaction

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Sales & Marketing", layout="wide")
st.title("📈 Sales & Marketing — Deep Guest Analysis")
st.caption("Historical context + forward projection. No scanning.")

# ==================================================
# STATE
# ==================================================
init_rooms(st.session_state)
rooms = st.session_state.rooms

if "transaction_ledger" not in st.session_state:
    st.session_state.transaction_ledger = []

if not rooms:
    st.info("No guests in-house yet. Run Auto Scan first.")
    st.stop()

engine = SLEDEngine()

# ==================================================
# SELECT GUEST
# ==================================================
ticker = st.selectbox("Select in-house guest", sorted(rooms.keys()))
room = rooms[ticker]

st.write(f"**Check-ins:** {len(room.get('History', []))}")
st.write(f"**Avg Signal Quality:** {room.get('Avg_Signal_Quality', 0.0)}")

# ==================================================
# LOAD DATA
# ==================================================
df = safe_history(ticker)
if df is None or df.empty:
    st.error("No price data available.")
    st.stop()

dfp = engine.calculate(df)
summary = engine.summarize(dfp)

# ==================================================
# BUILD PROJECTION DATA (SAFE SHAPES)
# ==================================================
close = df["Close"]
dates = close.index

last_date = dates[-1]
last_price = float(close.iloc[-1])

days_ahead = 7
future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]

vol = float(dfp["Rolling_Std"].iloc[-1])
energy = max(float(dfp["Sigma"].iloc[-1]), 0.1)

bias = 0
if summary["Signal"] == "BUY":
    bias = 1
elif summary["Signal"] == "SELL":
    bias = -1

proj_pct = vol * energy * np.sqrt(days_ahead)

# ---- Build flat arrays ----
x_proj = [last_date] + future_dates

y_path = [last_price]
y_upper = [last_price]
y_lower = [last_price]

for i in range(1, days_ahead + 1):
    factor = i / days_ahead
    y_path.append(last_price * (1 + bias * proj_pct * factor))
    y_upper.append(last_price * (1 + abs(proj_pct) * factor))
    y_lower.append(last_price * (1 - abs(proj_pct) * factor))

# ==================================================
# PLOT
# ==================================================
st.subheader("📊 Price History & 7-Day SLED Projection")

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(dates, close.values, label="Historical", color="white", lw=2)
ax.plot(x_proj, y_path, "--", lw=2, label="Projection")

ax.fill_between(
    x_proj,
    y_lower,
    y_upper,
    alpha=0.2,
    label="Forecast Cone"
)

ax.set_title(f"{ticker} — History & 7-Day Projection")
ax.grid(alpha=0.2)
ax.legend()

st.pyplot(fig)

# ==================================================
# METRICS
# ==================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Price", round(summary["Price"], 2))
c2.metric("SLED Signal", summary["Signal"])
c3.metric("Gate", round(summary["Gate"], 3))
c4.metric("Sigma", round(summary["Sigma"], 3))

# ==================================================
# DEEP REPORT
# ==================================================
st.divider()
st.subheader("🧠 Deep 30-Day Guest Report")

if st.button("📄 RUN DEEP REPORT", type="primary"):

    last_30 = df.tail(30)
    ret_30 = (last_30["Close"].iloc[-1] - last_30["Close"].iloc[0]) / last_30["Close"].iloc[0]

    raw_text = (
        f"{ticker} deep report | "
        f"30d_return={round(ret_30*100,2)}% | "
        f"SLED={summary['Signal']} | "
        f"Gate={round(summary['Gate'],3)} | "
        f"Sigma={round(summary['Sigma'],3)} | "
        f"Z={round(summary['Z_Trap'],3)}"
    )

    tx = admit_transaction(
        source="DEEP_REPORT",
        raw_text=raw_text
    )

    st.session_state.transaction_ledger.insert(0, tx)
    st.success("Deep report admitted via Doorman")

# ==================================================
# PREVIEW
# ==================================================
st.divider()
st.subheader("📜 Latest Intelligence")

st.dataframe(
    st.session_state.transaction_ledger[:15],
    use_container_width=True
)