import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- A7DO ARCHITECTURAL LAYERS ---

class WorldPatternLayer:
    """Layer 1: Statistical Emergence - Observing the 'Squeeze'"""
    @staticmethod
    def extract_patterns(df, decay=0.92):
        df = df.copy()
        df['returns'] = df['Close'].pct_change().fillna(0)
        df['sigma'] = df['returns'].rolling(5).std().fillna(0)
        
        # Z: The Structural Constraint (The 'Swerve' detector)
        delta = df['Close'].diff().abs().fillna(0)
        norm = (df['sigma'] * df['Close']) + 1e-6
        df['z_score'] = (1 - (delta / norm)).clip(0, 1)
        
        # E_Int: The Thermodynamic Pressure
        e_acc = 0
        e_history = []
        for s in df['sigma']:
            e_acc = e_acc * decay + s
            e_history.append(e_acc)
        df['entropy_integral'] = e_history
        return df

class EmbodimentLayer:
    """Layer 2: Biological Preference - Managing 'Vitality' (Drawdown)"""
    def __init__(self, dd_limit):
        self.dd_limit = dd_limit
        
    def get_vitality_state(self, current_equity, peak_equity):
        drawdown = (peak_equity - current_equity) / peak_equity
        # Vitality is 1.0 at peak, 0.0 at dd_limit
        vitality = max(0, 1 - (drawdown / self.dd_limit))
        return vitality, drawdown

class LogicalBridge:
    """Layer 3: Syllogistic Intent - Decision Gate"""
    def __init__(self, z_thresh, e_thresh):
        self.z_thresh = z_thresh
        self.e_thresh = e_thresh
        self.last_action = "LONG" # Initial State

    def decide(self, z, e_int, vitality):
        """
        Syllogism: 
        Premise A: Pattern is a Trap (Z high, E high)
        Premise B: Vitality is threatened (Vitality low)
        Conclusion: Swerve (Hedge)
        """
        is_trap = (z > self.z_thresh and e_int > self.e_thresh)
        is_weak = (vitality < 0.2) # High danger zone
        
        if is_trap or is_weak:
            self.last_action = "HEDGED"
            return 1.0 # 100% Cash
            
        # Hysteresis: Only re-enter if Entropy has 'Cooled'
        if self.last_action == "HEDGED":
            if e_int < (self.e_thresh * 0.7): # Cooling threshold
                self.last_action = "LONG"
                return 0.0
            else:
                return 1.0 # Stay hedged
                
        return 0.0

class CollectiveLayer:
    """Layer 4: Social Stability - Signal Smoothing"""
    @staticmethod
    def smooth_signals(signals, window=3):
        # Prevents 'Panic Loops' by ensuring signals are persistent
        return pd.Series(signals).rolling(window).mean().fillna(0)

# --- APPLICATION ENGINE ---

st.set_page_config(layout="wide", page_title="SLED A7DO Architecture")
st.title("🏛️ SLED_AI: A7DO Multi-Layer Architecture")

with st.sidebar:
    st.header("A7DO Parameters")
    ticker = st.text_input("Asset", "SPY")
    z_limit = st.slider("World Pattern: Z-Thresh", 0.60, 0.95, 0.85)
    e_limit = st.slider("World Pattern: E-Thresh", 0.01, 0.10, 0.04)
    dd_limit = st.slider("Embodiment: Max DD", 0.05, 0.20, 0.10)
    smooth_w = st.slider("Collective: Smoothing", 1, 10, 3)

@st.cache_data
def run_a7do_sim(symbol, z_t, e_t, dd_t, s_w):
    raw = yf.download(symbol, start="2010-01-01", progress=False)
    if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
    
    # 1. World Pattern
    df = WorldPatternLayer.extract_patterns(raw)
    
    # 2 & 3. Embodiment & Logical Bridge
    body = EmbodimentLayer(dd_t)
    bridge = LogicalBridge(z_t, e_t)
    
    cash = 100000
    shares = cash / df['Close'].iloc[0]
    cash = 0
    peak = 100000
    
    equities = []
    raw_signals = []
    
    for i in range(len(df)):
        price = df['Close'].iloc[i]
        curr_nav = cash + (shares * price)
        peak = max(peak, curr_nav)
        
        vit, dd = body.get_vitality_state(curr_nav, peak)
        hedge_ratio = bridge.decide(df['z_score'].iloc[i], df['entropy_integral'].iloc[i], vit)
        raw_signals.append(hedge_ratio)
        
        # Collective Smoothing (Simulated in loop)
        if i > s_w:
            smoothed_hr = np.mean(raw_signals[-s_w:])
        else:
            smoothed_hr = hedge_ratio
            
        # Execution
        target_cash = curr_nav * smoothed_hr
        if cash < target_cash:
            to_sell = (target_cash - cash) / price
            shares_sold = min(shares, to_sell)
            shares -= shares_sold
            cash += shares_sold * price
        elif smoothed_hr == 0 and cash > 0:
            shares += cash / price
            cash = 0
            
        equities.append(cash + shares * price)
        
    df['equity'] = equities
    df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    return df

results = run_a7do_sim(ticker, z_limit, e_limit, dd_limit, smooth_w)

# UI Display
c1, c2, c3 = st.columns(3)
c1.metric("A7DO Final Equity", f"${results['equity'].iloc[-1]:,.0f}")
c2.metric("Max Drawdown", f"{results['drawdown'].max()*100:.2f}%")
c3.metric("B&H Performance", f"{(results['Close'].iloc[-1]/results['Close'].iloc[0]-1)*100:.2f}%")

fig = go.Figure()
fig.add_trace(go.Scatter(x=results.index, y=results['equity'], name="A7DO Strategy", line=dict(color="#10b981")))
fig.add_trace(go.Scatter(x=results.index, y=(results['Close']/results['Close'].iloc[0]*100000), name="Market", line=dict(color="#475569", dash="dot")))
fig.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig, use_container_width=True)

st.info("The Logical Bridge facilitates purposeful agency by combining World-Pattern observations with Embodiment vitality needs.")

