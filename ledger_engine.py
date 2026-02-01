"""
ledger_engine.py
----------------
Authoritative SLED Ledger Engine (Pandas-safe)

Exports:
- init_ledgers
- log_signal
- update_outcomes
- update_attribution
"""

import pandas as pd
import numpy as np
from sled_core import safe_history


# ==================================================
# INITIALISE LEDGERS
# ==================================================

def init_ledgers(state):
    if "signal_ledger" not in state:
        state.signal_ledger = pd.DataFrame(
            columns=[
                "Timestamp",
                "Ticker",
                "Raw_Signal",
                "Final_Action",
                "Gate",
                "Z_Trap",
                "Sigma",
                "RiseScore_14d",
                "Bullseye",
                "Decision_Reason",
            ]
        )

    if "outcome_ledger" not in state:
        state.outcome_ledger = pd.DataFrame(
            columns=[
                "Timestamp",
                "Ticker",
                "Price_At_Decision",
                "Price_+14d",
                "Max_Drawdown_%",
                "Max_Runup_%",
            ]
        )

    if "attribution_ledger" not in state:
        state.attribution_ledger = pd.DataFrame(
            columns=[
                "Timestamp",
                "Ticker",
                "Final_Action",
                "Decision_Quality",
                "Avoided_Loss_%",
                "Missed_Gain_%",
            ]
        )


# ==================================================
# SIGNAL LEDGER (WRITE ONCE)
# ==================================================

def log_signal(state, row: dict):
    state.signal_ledger = pd.concat(
        [state.signal_ledger, pd.DataFrame([row])],
        ignore_index=True
    )


# ==================================================
# OUTCOME LEDGER
# ==================================================

def update_outcomes(state):
    for _, s in state.signal_ledger.iterrows():

        exists = (
            (state.outcome_ledger["Ticker"] == s["Ticker"]) &
            (state.outcome_ledger["Timestamp"] == s["Timestamp"])
        ).any()

        if exists:
            continue

        df = safe_history(s["Ticker"], period="1mo")
        if df is None or df.empty:
            continue

        try:
            price_at = float(df["Close"].iloc[0])
            price_14 = float(df["Close"].iloc[-1])
            drawdown = float((df["Close"].min() - price_at) / price_at * 100)
            runup = float((df["Close"].max() - price_at) / price_at * 100)
        except Exception:
            continue

        row = {
            "Timestamp": s["Timestamp"],
            "Ticker": s["Ticker"],
            "Price_At_Decision": round(price_at, 3),
            "Price_+14d": round(price_14, 3),
            "Max_Drawdown_%": round(drawdown, 2),
            "Max_Runup_%": round(runup, 2),
        }

        state.outcome_ledger = pd.concat(
            [state.outcome_ledger, pd.DataFrame([row])],
            ignore_index=True
        )


# ==================================================
# ATTRIBUTION LEDGER (PANDAS-SAFE)
# ==================================================

def update_attribution(state):
    for _, o in state.outcome_ledger.iterrows():

        exists = (
            (state.attribution_ledger["Ticker"] == o["Ticker"]) &
            (state.attribution_ledger["Timestamp"] == o["Timestamp"])
        ).any()

        if exists:
            continue

        s = state.signal_ledger[
            (state.signal_ledger["Ticker"] == o["Ticker"]) &
            (state.signal_ledger["Timestamp"] == o["Timestamp"])
        ]

        if s.empty:
            continue

        s = s.iloc[0]

        # ---- EXPLICIT SCALAR CASTS (CRITICAL) ----
        max_dd = float(o["Max_Drawdown_%"])
        max_ru = float(o["Max_Runup_%"])
        action = str(s["Final_Action"])

        quality = "NEUTRAL"
        avoided = 0.0
        missed = 0.0

        if action == "WAIT":
            if max_dd < -2.0:
                quality = "CORRECT"
                avoided = abs(max_dd)
            elif max_ru > 5.0:
                quality = "INCORRECT"
                missed = max_ru

        elif action == "BUY":
            if max_ru > 5.0:
                quality = "CORRECT"
            elif max_dd < -3.0:
                quality = "INCORRECT"

        elif action == "SELL":
            if max_dd < -5.0:
                quality = "CORRECT"
            elif max_ru > 5.0:
                quality = "INCORRECT"

        row = {
            "Timestamp": o["Timestamp"],
            "Ticker": o["Ticker"],
            "Final_Action": action,
            "Decision_Quality": quality,
            "Avoided_Loss_%": round(avoided, 2),
            "Missed_Gain_%": round(missed, 2),
        }

        state.attribution_ledger = pd.concat(
            [state.attribution_ledger, pd.DataFrame([row])],
            ignore_index=True
        )