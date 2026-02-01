import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sled_core import safe_history

def init_ledgers(state):
    if "signal_ledger" not in state: state.signal_ledger = pd.DataFrame()
    if "outcome_ledger" not in state: state.outcome_ledger = pd.DataFrame()
    if "attribution_ledger" not in state: state.attribution_ledger = pd.DataFrame()

def log_signal(state, row: dict):
    state.signal_ledger = pd.concat(
        [state.signal_ledger, pd.DataFrame([row])], ignore_index=True
    )

def update_outcomes(state):
    for _, r in state.signal_ledger.iterrows():
        if not ((state.outcome_ledger["Ticker"]==r.Ticker) &
                (state.outcome_ledger["Timestamp"]==r.Timestamp)).any():
            df = safe_history(r.Ticker,"1mo")
            if df is None: continue
            p0 = float(df.Close.iloc[-1])
            p14 = float(df.Close.iloc[-1])
            dd = (df.Close.min()-p0)/p0*100
            ru = (df.Close.max()-p0)/p0*100
            state.outcome_ledger = pd.concat([
                state.outcome_ledger,
                pd.DataFrame([{
                    "Ticker": r.Ticker,
                    "Timestamp": r.Timestamp,
                    "Price_At": p0,
                    "Price_+14d": p14,
                    "Max_Drawdown_%": dd,
                    "Max_Runup_%": ru
                }])
            ])

def update_attribution(state):
    for _, o in state.outcome_ledger.iterrows():
        if not ((state.attribution_ledger["Ticker"]==o.Ticker) &
                (state.attribution_ledger["Timestamp"]==o.Timestamp)).any():
            s = state.signal_ledger[
                (state.signal_ledger.Ticker==o.Ticker) &
                (state.signal_ledger.Timestamp==o.Timestamp)
            ].iloc[0]
            quality="NEUTRAL"
            if s.Final_Action=="WAIT" and o.Max_Drawdown_%<-2:
                quality="CORRECT"
            elif s.Final_Action=="BUY" and o.Max_Runup_%>5:
                quality="CORRECT"
            state.attribution_ledger = pd.concat([
                state.attribution_ledger,
                pd.DataFrame([{
                    "Ticker": o.Ticker,
                    "Timestamp": o.Timestamp,
                    "Final_Action": s.Final_Action,
                    "Decision_Quality": quality,
                    "Avoided_Loss_%": abs(o.Max_Drawdown_%) if s.Final_Action=="WAIT" else 0
                }])
            ])