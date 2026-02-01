"""
warp_engine.py
--------------
Warp State Classification for SLED
"""

import pandas as pd


def classify_warp(outcome_row, attribution_row):
    """
    Determine Warp state from measured outcomes.
    """
    max_ru = float(outcome_row["Max_Runup_%"])
    max_dd = float(outcome_row["Max_Drawdown_%"])
    action = attribution_row["Final_Action"]
    quality = attribution_row["Decision_Quality"]

    if max_ru >= 8.0 and max_ru > abs(max_dd):
        return "WARP_UP"

    if max_dd <= -8.0 and abs(max_dd) > max_ru:
        return "WARP_DOWN"

    if action != "WAIT" and quality == "NEUTRAL":
        return "PRE_WARP"

    return "POST_WARP"


def update_warp_states(state):
    """
    Adds Warp_State column to attribution ledger.
    """
    if state.attribution_ledger.empty or state.outcome_ledger.empty:
        return

    if "Warp_State" not in state.attribution_ledger.columns:
        state.attribution_ledger["Warp_State"] = ""

    for idx, a in state.attribution_ledger.iterrows():
        if a["Warp_State"]:
            continue

        o = state.outcome_ledger[
            (state.outcome_ledger["Ticker"] == a["Ticker"]) &
            (state.outcome_ledger["Timestamp"] == a["Timestamp"])
        ]

        if o.empty:
            continue

        warp = classify_warp(o.iloc[0], a)
        state.attribution_ledger.at[idx, "Warp_State"] = warp