import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- A7DO PHASE-LOCKED ARCHITECTURE ---

class WorldPatternLayer:
    """Layer 1: Identifies the 'Squeeze' and 'Flow'"""
    @staticmethod
    def extract_patterns(df, decay=0.92):
        df = df.copy()
        df['returns'] = df['Close'].pct_change().fillna(0)
        df['sigma'] = df['returns'].rolling(12).std().fillna(0)
        
        # Z-Score: Structural Constraint
        delta = df['Close'].diff().abs().fillna(0)
        norm = (df['sigma'] * df['Close']) + 1e-6
        df['z_score'] = (1 - (delta / norm)).clip(0, 1)
        
        # Entropy: Thermodynamic Pressure
        e_acc = 0
        e_history = []
        for s in df['sigma']:
            e_acc = (e_acc * decay) + s
            e_history.append(e_acc)
        df['entropy_integral'] = e_history
        return df

class LogicalBridge:
    """Layer 3: RE-ENTRY OVERDRIVE - Solving the -0.46% CAGR"""
    def __init__(self, z_thresh, e_thresh):
        self.z_thresh = z_thresh
        self.e_thresh = e_thresh
        self.state = "LONG"
        self.entry_price = 0

    def decide(self, z, e_int, current_price, vitality):
        # 1. DEFENSIVE SWERVE (Keep the 8% DD Protection)
        if (z > self.z_thresh and e_int > self.e_thresh) or vitality < 0.2:
            if self.state == "LONG":
                self.entry_price = current_price
            self.state = "HEDGED"
            return 1.0
            
        # 2. PHASE-LOCKED RE-ENTRY (The Alpha Fix)
        if self.state == "HEDGED":
            # RE-ENTRY CONDITION A: Standard Cooling
            cooled = e_int < (self.e_thresh * 0.4)
            # RE-ENTRY CONDITION B: Momentum Breakout (Market is leaving us behind)
            # If price rises 2.5% above where we hedged, the 'Trap' was a false positive
            breakout = current_price > (self.entry_price * 1.025)
            
            if cooled or breakout or z < 0.3:
                self.state = "LONG"
                return 0.0
            return 1.0
                
        return 0.0

# --- SIMULATION CORE ---

st.set_page_config(layout="wide", page_title="SLED A7DO Phase-Lock")
st.title("🚀 SLED_AI: A7DO Phase-Locked Recovery")

with st.sidebar:
    st.header("A7DO Parameters")
    ticker = st.text_input("Ticker", "SPY")
    lookback = st.number_input("Lookback Years", 1, 20, 10)
    
    st.subheader("Logical Bridge")
    z_limit = st.slider("Exit Z-Thresh", 0.70, 0.95, 0.88)
    e_limit = st.slider("Exit E-Thresh", 0.02, 0.08, 0.04)
    
    st.subheader("Collective Layer")
    smooth_window = st.slider("Smoothing (Social Friction)", 1, 15, 5)

@st.cache_data
def run_simulation(symbol, yrs, z_t, e_t, s_w):
    start = datetime.now() - timedelta(days=365*yrs)
    df = yf.download(symbol, start=start, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    df = WorldPatternLayer.extract_patterns(df)
    bridge = LogicalBridge(z_t, e_t)
    
    cash, shares, peak = 100000, 0, 100000
    shares = cash / df['Close'].iloc[0]
    cash = 0
    
    history, signals = [], []
    
    for i in range(len(df)):
        p = df['Close'].iloc[i]
        nav = cash + (shares * p)
        peak = max(peak, nav)
        vit = max(0, 1 - ((peak - nav) / (peak * 0.12))) # 12% DD Hard Floor
        
        # Decision
        raw_h = bridge.decide(df['z_score'].iloc[i], df['entropy_integral'].iloc[i], p, vit)
        signals.append(raw_h)
        
        # Collective Smoothing
        h = np.mean(signals[-s_w:]) if i >= s_w else raw_h
        
        # Rebalance
        target_cash = nav * h
        if cash < target_cash:
            to_sell = (target_cash - cash) / p
            s_sold = min(shares, to_sell)
            shares -= s_sold
            cash += s_sold * p
        elif h < 0.05 and cash > 0:
            shares += cash / p
            cash = 0
            
        history.append(cash + shares * p)
        
    df['equity'] = history
    df['bh'] = (df['Close'] / df['Close'].iloc[0]) * 100000
    df['dd'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    return df

res = run_simulation(ticker, lookback, z_limit, e_limit, smooth_window)

if res is not None:
    c1, c2, c3 = st.columns(3)
    final_cagr = (res['equity'].iloc[-1] / 100000)**(1/lookback) - 1
    c1.metric("Final CAGR", f"{final_cagr*100:.2f}%")
    c2.metric("Max Drawdown", f"{res['dd'].max()*100:.2f}%")
    c3.metric("Final Capital", f"${res['equity'].iloc[-1]:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res.index, y=res['bh'], name="Market", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=res.index, y=res['equity'], name="SLED Phase-Locked", line=dict(color="#00ffcc", width=3)))
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

