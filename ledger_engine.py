"""
ledger_engine.py
----------------
Authoritative SLED Ledger Engine

Exports EXACTLY:
- init_ledgers
- log_signal
- update_outcomes
- update_attribution
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
    """
    row MUST contain:
    Timestamp, Ticker, Raw_Signal, Final_Action,
    Gate, Z_Trap, Sigma, RiseScore_14d, Bullseye, Decision_Reason
    """
    state.signal_ledger = pd.concat(
        [state.signal_ledger, pd.DataFrame([row])],
        ignore_index=True
    )


# ==================================================
# OUTCOME LEDGER
# ==================================================

def update_outcomes(state):
    """
    For each signal not yet evaluated, compute outcomes.
    """
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
            drawdown = (df["Close"].min() - price_at) / price_at * 100
            runup = (df["Close"].max() - price_at) / price_at * 100
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
# ATTRIBUTION LEDGER
# ==================================================

def update_attribution(state):
    """
    Attribute correctness AFTER outcomes exist.
    """
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

        quality = "NEUTRAL"
        avoided = 0.0
        missed = 0.0

        if s["Final_Action"] == "WAIT":
            if o["Max_Drawdown_%"] < -2:
                quality = "CORRECT"
                avoided = abs(o["Max_Drawdown_%"])
        elif s["Final_Action"] == "BUY":
            if o["Max_Runup_%"] > 5:
                quality = "CORRECT"
            elif o["Max_Drawdown_%"] < -3:
                quality = "INCORRECT"
        elif s["Final_Action"] == "SELL":
            if o["Max_Drawdown_%"] < -5:
                quality = "CORRECT"

        row = {
            "Timestamp": o["Timestamp"],
            "Ticker": o["Ticker"],
            "Final_Action": s["Final_Action"],
            "Decision_Quality": quality,
            "Avoided_Loss_%": round(avoided, 2),
            "Missed_Gain_%": round(missed, 2),
        }

        state.attribution_ledger = pd.concat(
            [state.attribution_ledger, pd.DataFrame([row])],
            ignore_index=True
        )