import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SLED V4: GHOST FLOW ARCHITECTURE ---

class WorldPatternLayer:
    """Layer 1: Structural Squeezes & Ghost Momentum"""
    @staticmethod
    def extract_patterns(df):
        df = df.copy()
        df['returns'] = df['Close'].pct_change().fillna(0)
        
        # 1. Structural Squeeze (The Exit Trigger)
        sigma = df['returns'].rolling(15).std().fillna(0)
        delta = df['Close'].diff().abs().fillna(0)
        df['z_score'] = (1 - (delta / (sigma * df['Close'] + 1e-6))).clip(0, 1)
        
        # 2. Ghost Flow (The Recovery Pull)
        # 20-day price momentum as a 'Ghost' that pulls us back in
        df['ghost_pull'] = df['Close'].pct_change(20).fillna(0)
        
        # 3. Pressure
        df['entropy'] = df['returns'].rolling(10).std().fillna(0)
        return df

class LogicalBridge:
    """Layer 3: Purposeful Agency - The Ghost Flow Re-entry"""
    def __init__(self, z_thresh, ghost_thresh):
        self.z_thresh = z_thresh
        self.ghost_thresh = ghost_thresh
        self.state = "LONG"

    def decide(self, z, ghost, vitality):
        # 1. THE SWERVE (Protection)
        # Exit if Z-Score is high OR vitality is failing
        if z > self.z_thresh or vitality < 0.25:
            self.state = "HEDGED"
            return 1.0 # 100% Cash
            
        # 2. THE GHOST PULL (Aggressive Recovery)
        if self.state == "HEDGED":
            # If the 'Ghost' (Market) has risen significantly, it overrides fear
            if ghost > self.ghost_thresh or z < 0.4:
                self.state = "LONG"
                return 0.0
            return 1.0
                
        return 0.0

# --- SIMULATION CORE ---

st.set_page_config(layout="wide", page_title="SLED V4 Ghost Flow")
st.title("👻 SLED_AI: Ghost Flow Engine (V4)")

with st.sidebar:
    st.header("V4 Parameters")
    ticker = st.text_input("Ticker", "SPY")
    lookback = st.slider("Years", 5, 20, 15)
    
    st.subheader("Sensors")
    z_limit = st.slider("Exit Sensitivity (Z)", 0.70, 0.95, 0.85)
    g_pull = st.slider("Ghost Pull (Re-entry %)", 0.01, 0.10, 0.04)
    
    st.subheader("Collective")
    smooth = st.slider("Smooth Window", 1, 10, 3)

@st.cache_data
def run_v4(symbol, yrs, z_t, g_t, s_v):
    try:
        start = datetime.now() - timedelta(days=365*yrs)
        df = yf.download(symbol, start=start, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = WorldPatternLayer.extract_patterns(df)
        bridge = LogicalBridge(z_t, g_t)
        
        cash, shares, peak = 100000, 0, 100000
        shares = cash / df['Close'].iloc[0]
        cash = 0
        
        history, signals = [], []
        
        for i in range(len(df)):
            p = df['Close'].iloc[i]
            nav = cash + (shares * p)
            peak = max(peak, nav)
            
            # Vitality (15% Target DD)
            vit = max(0, 1 - ((peak - nav) / (peak * 0.15)))
            
            # Decision
            h_raw = bridge.decide(df['z_score'].iloc[i], df['ghost_pull'].iloc[i], vit)
            signals.append(h_raw)
            
            # Exposure Calculation
            h = np.mean(signals[-s_v:]) if i >= s_v else h_raw
            
            # Rebalance Logic
            target_cash = nav * h
            if cash < target_cash:
                to_sell = (target_cash - cash) / p
                qty = min(shares, to_sell)
                shares -= qty
                cash += qty * p
            elif h < 0.1 and cash > 0:
                shares += cash / p
                cash = 0
                
            history.append(cash + shares * p)
            
        df['equity'] = history
        df['bh'] = (df['Close'] / df['Close'].iloc[0]) * 100000
        df['dd'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
        return df
    except Exception as e:
        st.error(f"Engine Error: {e}")
        return None

res = run_v4(ticker, lookback, z_limit, g_pull, smooth)

if res is not None:
    c1, c2, c3 = st.columns(3)
    yrs_act = (res.index[-1] - res.index[0]).days / 365.25
    cagr = (res['equity'].iloc[-1] / 100000)**(1/yrs_act) - 1
    bh_cagr = (res['bh'].iloc[-1] / 100000)**(1/yrs_act) - 1
    
    c1.metric("V4 CAGR", f"{cagr*100:.2f}%", delta=f"{(cagr-bh_cagr)*100:.2f}%")
    c2.metric("Max DD", f"{res['dd'].max()*100:.2f}%")
    c3.metric("Final Capital", f"${res['equity'].iloc[-1]:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res.index, y=res['bh'], name="Market (B&H)", line=dict(color="gray", width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=res.index, y=res['equity'], name="SLED Ghost Flow", line=dict(color="#f472b6", width=2.5)))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,b=0,t=20))
    st.plotly_chart(fig, use_container_width=True)

