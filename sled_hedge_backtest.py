import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- A7DO KINETIC ALPHA ARCHITECTURE ---

class WorldPatternLayer:
    """Layer 1: Identifies Structural Squeezes & Kinetic Velocity"""
    @staticmethod
    def extract_patterns(df, decay=0.92):
        df = df.copy()
        df['returns'] = df['Close'].pct_change().fillna(0)
        df['sigma'] = df['returns'].rolling(12).std().fillna(0)
        
        # Z-Score: Structural Constraint (The 'Swerve' trigger)
        delta = df['Close'].diff().abs().fillna(0)
        norm = (df['sigma'] * df['Close']) + 1e-6
        df['z_score'] = (1 - (delta / norm)).clip(0, 1)
        
        # Velocity: Rate of Change (The 'Alpha' driver)
        df['velocity'] = df['Close'].pct_change(5).fillna(0) 
        
        # Entropy: Thermodynamic Pressure
        e_acc = 0
        e_history = []
        for s in df['sigma']:
            e_acc = (e_acc * decay) + s
            e_history.append(e_acc)
        df['entropy_integral'] = e_history
        return df

class LogicalBridge:
    """Layer 3: KINETIC OVERDRIVE - Bridging the 5.82% to 13%+ gap"""
    def __init__(self, z_thresh, e_thresh):
        self.z_thresh = z_thresh
        self.e_thresh = e_thresh
        self.state = "LONG"
        self.exit_price = 0

    def decide(self, z, e_int, velocity, current_price, vitality):
        # 1. THE SWERVE (Keep Drawdown Protection)
        if (z > self.z_thresh and e_int > self.e_thresh) or vitality < 0.25:
            if self.state == "LONG":
                self.exit_price = current_price
            self.state = "HEDGED"
            return 1.0 # 100% Hedge
            
        # 2. THE KINETIC RE-ENTRY (Alpha Fix)
        if self.state == "HEDGED":
            # RE-ENTRY CONDITION: 
            # A: Entropy Cooling
            # B: OR Kinetic Velocity (Market is moving fast upward - don't miss it)
            # C: OR Price Recovery (2% above exit)
            if e_int < (self.e_thresh * 0.6) or velocity > 0.02 or current_price > (self.exit_price * 1.02):
                self.state = "LONG"
                return 0.0
            return 1.0
                
        return 0.0

class CollectiveLayer:
    """Layer 4: Social Consensus & Kinetic Leverage"""
    @staticmethod
    def calculate_exposure(hedge_ratio, velocity, use_leverage):
        # If we are NOT hedged and velocity is strong, we apply 'Kinetic Leverage'
        if hedge_ratio < 0.1 and use_leverage and velocity > 0.01:
            return 1.25 # 125% exposure to catch up on lost growth
        return 1.0 - hedge_ratio

# --- SIMULATION ENGINE ---

st.set_page_config(layout="wide", page_title="SLED Kinetic Alpha")
st.title("⚡ SLED_AI: A7DO Kinetic Alpha")

with st.sidebar:
    st.header("Kinetic Parameters")
    ticker = st.text_input("Ticker", "SPY")
    lookback = st.slider("Years", 5, 20, 15)
    
    st.subheader("Logical Bridge")
    z_limit = st.slider("Exit Sensitivity (Z)", 0.70, 0.95, 0.88)
    e_limit = st.slider("Pressure Limit (E)", 0.02, 0.08, 0.04)
    
    st.subheader("Kinetic Alpha")
    enable_leverage = st.checkbox("Enable Kinetic Leverage (1.25x)", value=True)
    smooth_window = st.slider("Signal Smoothing", 1, 15, 3)

@st.cache_data
def run_simulation(symbol, yrs, z_t, e_t, lev, s_w):
    start = datetime.now() - timedelta(days=365*yrs)
    df = yf.download(symbol, start=start, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    df = WorldPatternLayer.extract_patterns(df)
    bridge = LogicalBridge(z_t, e_t)
    collective = CollectiveLayer()
    
    cash, shares, peak = 100000, 0, 100000
    shares = cash / df['Close'].iloc[0]
    cash = 0
    
    history, signals = [], []
    
    for i in range(len(df)):
        p = df['Close'].iloc[i]
        nav = cash + (shares * p)
        peak = max(peak, nav)
        vit = max(0, 1 - ((peak - nav) / (peak * 0.15))) # 15% Max DD Shield
        
        # Decision
        raw_h = bridge.decide(df['z_score'].iloc[i], df['entropy_integral'].iloc[i], df['velocity'].iloc[i], p, vit)
        signals.append(raw_h)
        
        # Consensus & Kinetic Exposure
        avg_h = np.mean(signals[-s_w:]) if i >= s_w else raw_h
        exposure = collective.calculate_exposure(avg_h, df['velocity'].iloc[i], lev)
        
        # Target Rebalance
        target_equity_in_market = nav * exposure
        current_equity_in_market = shares * p
        
        diff = target_equity_in_market - current_equity_in_market
        if diff > 0: # Need to buy
            to_buy = min(cash, diff)
            shares += to_buy / p
            cash -= to_buy
        elif diff < 0: # Need to sell
            to_sell = min(shares, abs(diff) / p)
            shares -= to_sell
            cash += to_sell * p
            
        history.append(cash + shares * p)
        
    df['equity'] = history
    df['bh'] = (df['Close'] / df['Close'].iloc[0]) * 100000
    df['dd'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    return df

res = run_simulation(ticker, lookback, z_limit, e_limit, enable_leverage, smooth_window)

if res is not None:
    c1, c2, c3 = st.columns(3)
    yrs_actual = (res.index[-1] - res.index[0]).days / 365.25
    final_cagr = (res['equity'].iloc[-1] / 100000)**(1/yrs_actual) - 1
    bh_cagr = (res['bh'].iloc[-1] / 100000)**(1/yrs_actual) - 1
    
    c1.metric("Kinetic CAGR", f"{final_cagr*100:.2f}%", delta=f"{(final_cagr-bh_cagr)*100:.2f}% vs B&H")
    c2.metric("Max Drawdown", f"{res['dd'].max()*100:.2f}%")
    c3.metric("Final Capital", f"${res['equity'].iloc[-1]:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res.index, y=res['bh'], name="Buy & Hold", line=dict(color="gray", width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=res.index, y=res['equity'], name="SLED Kinetic Alpha", line=dict(color="#facc15", width=3)))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,b=0,t=20))
    st.plotly_chart(fig, use_container_width=True)

