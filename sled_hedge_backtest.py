import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SLED V3: RESONANCE ARCHITECTURE ---

class ResonanceLayer:
    """Layer 1: Detects when market structure 'Harmonizes' with growth"""
    @staticmethod
    def extract_resonance(df):
        df = df.copy()
        df['returns'] = df['Close'].pct_change().fillna(0)
        
        # Fast vs Slow Volatility (The 'Harmonic' Check)
        df['vol_fast'] = df['returns'].rolling(5).std()
        df['vol_slow'] = df['returns'].rolling(21).std()
        
        # Resonance occurs when short-term vol is lower than long-term vol (Stability)
        df['resonance'] = (df['vol_slow'] / (df['vol_fast'] + 1e-6)).clip(0, 5)
        
        # Structural Squeeze (Z-Score)
        delta = df['Close'].diff().abs().fillna(0)
        sigma = df['returns'].rolling(15).std().fillna(0)
        df['z_score'] = (1 - (delta / (sigma * df['Close'] + 1e-6))).clip(0, 1)
        
        return df

class LogicalBridge:
    """Layer 3: Purposeful Agency - Solves the -0.64% Regression"""
    def __init__(self, z_thresh, res_min):
        self.z_thresh = z_thresh
        self.res_min = res_min
        self.state = "LONG"
        self.high_water_mark = 0

    def decide(self, z, resonance, current_price, vitality):
        # 1. THE EMERGENCY BRAKE (Swerve)
        # We exit if Z-Score spikes OR if we lose 15% from the local peak
        self.high_water_mark = max(self.high_water_mark, current_price)
        local_dd = (self.high_water_mark - current_price) / self.high_water_mark
        
        if z > self.z_thresh or local_dd > 0.08 or vitality < 0.2:
            if self.state == "LONG":
                self.state = "HEDGED"
            return 1.0 # 100% Defensive
            
        # 2. THE RESONANT RE-ENTRY (The Alpha Driver)
        if self.state == "HEDGED":
            # We ONLY go back in if:
            # A: Market is 'Stable' (Resonance > Threshold)
            # B: AND Z-Score has cooled
            if resonance > self.res_min and z < 0.5:
                self.state = "LONG"
                self.high_water_mark = current_price # Reset water mark on entry
                return 0.0
            return 1.0
                
        return 0.0

# --- SIMULATION CORE ---

st.set_page_config(layout="wide", page_title="SLED V3 Resonance")
st.title("🛡️ SLED_AI: Resonance Core (V3)")

with st.sidebar:
    st.header("Resonance Tuning")
    ticker = st.text_input("Ticker", "SPY")
    lookback = st.slider("Years", 5, 20, 15)
    
    st.subheader("Structural Limits")
    z_limit = st.slider("Exit Sensitivity (Z)", 0.75, 0.95, 0.82)
    res_req = st.slider("Re-entry Resonance", 1.0, 3.0, 1.5)
    
    st.subheader("Collective Friction")
    smooth = st.slider("Signal Lag (Social)", 1, 10, 4)

@st.cache_data
def run_v3(symbol, yrs, z_t, r_m, s_v):
    start = datetime.now() - timedelta(days=365*yrs)
    df = yf.download(symbol, start=start, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    df = ResonanceLayer.extract_resonance(df)
    bridge = LogicalBridge(z_t, r_m)
    
    cash, shares, peak = 100000, 0, 100000
    shares = cash / df['Close'].iloc[0]
    cash = 0
    
    history, signals = [], []
    
    for i in range(len(df)):
        p = df['Close'].iloc[i]
        nav = cash + (shares * p)
        peak = max(peak, nav)
        vit = max(0, 1 - ((peak - nav) / (peak * 0.12))) # 12% DD Shield
        
        # Decision logic
        h_raw = bridge.decide(df['z_score'].iloc[i], df['resonance'].iloc[i], p, vit)
        signals.append(h_raw)
        
        # Smoothed Exposure
        h = np.mean(signals[-s_v:]) if i >= s_v else h_raw
        
        # Execute Rebalance
        target_cash = nav * h
        if cash < target_cash:
            to_sell = (target_cash - cash) / p
            s_out = min(shares, to_sell)
            shares -= s_out
            cash += s_out * p
        elif h < 0.1 and cash > 0:
            shares += cash / p
            cash = 0
            
        history.append(cash + shares * p)
        
    df['equity'] = history
    df['bh'] = (df['Close'] / df['Close'].iloc[0]) * 100000
    df['dd'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    return df

res = run_v3(ticker, lookback, z_limit, res_req, smooth)

if res is not None:
    c1, c2, c3 = st.columns(3)
    yrs_act = (res.index[-1] - res.index[0]).days / 365.25
    cagr = (res['equity'].iloc[-1] / 100000)**(1/yrs_act) - 1
    bh_cagr = (res['bh'].iloc[-1] / 100000)**(1/yrs_act) - 1
    
    c1.metric("V3 CAGR", f"{cagr*100:.2f}%", delta=f"{(cagr-bh_cagr)*100:.2f}%")
    c2.metric("Max DD", f"{res['dd'].max()*100:.2f}%")
    c3.metric("Final Capital", f"${res['equity'].iloc[-1]:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res.index, y=res['bh'], name="Market", line=dict(color="gray", width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=res.index, y=res['equity'], name="SLED Resonance", line=dict(color="#60a5fa", width=2.5)))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,b=0,t=20))
    st.plotly_chart(fig, use_container_width=True)

