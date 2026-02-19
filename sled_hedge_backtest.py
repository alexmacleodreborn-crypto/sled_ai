import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- A7DO RECOVERY ARCHITECTURE ---

class WorldPatternLayer:
    """Layer 1: Statistical Emergence - Enhanced Squeeze Detection"""
    @staticmethod
    def extract_patterns(df, decay=0.92):
        df = df.copy()
        df['returns'] = df['Close'].pct_change().fillna(0)
        # 10-day window for stability
        df['sigma'] = df['returns'].rolling(10).std().fillna(0)
        
        # Z: The Structural Constraint (Swerve detector)
        delta = df['Close'].diff().abs().fillna(0)
        norm = (df['sigma'] * df['Close']) + 1e-6
        df['z_score'] = (1 - (delta / norm)).clip(0, 1)
        
        # E_Int: The Thermodynamic Pressure
        e_acc = 0
        e_history = []
        for s in df['sigma']:
            e_acc = (e_acc * decay) + s
            e_history.append(e_acc)
        df['entropy_integral'] = e_history
        return df

class EmbodimentLayer:
    """Layer 2: Biological Preference - Dynamic Vitality"""
    def __init__(self, dd_limit):
        self.dd_limit = dd_limit
        
    def get_vitality_state(self, current_equity, peak_equity):
        drawdown = (peak_equity - current_equity) / peak_equity
        vitality = max(0, 1 - (drawdown / self.dd_limit))
        return vitality, drawdown

class LogicalBridge:
    """Layer 3: ASYMMETRIC Syllogistic Intent - Agile Re-entry"""
    def __init__(self, z_thresh, e_thresh):
        self.z_thresh = z_thresh
        self.e_thresh = e_thresh
        self.state = "LONG" 

    def decide(self, z, e_int, vitality):
        # 1. TRIGGER EXIT (High Pressure + High Constraint)
        if (z > self.z_thresh and e_int > self.e_thresh) or vitality < 0.15:
            self.state = "HEDGED"
            return 1.0 
            
        # 2. TRIGGER ASYMMETRIC RE-ENTRY
        if self.state == "HEDGED":
            # RE-ENTRY: Entropy cooled 50% OR Z-Score 'Releases' (Z < 0.4)
            if e_int < (self.e_thresh * 0.5) or z < 0.4:
                self.state = "LONG"
                return 0.0
            else:
                return 1.0
                
        return 0.0

# --- EXECUTION ENGINE ---

st.set_page_config(layout="wide", page_title="SLED A7DO Recovery")
st.title("🧠 SLED_AI: A7DO Recovery Engine")

with st.sidebar:
    st.header("🎛️ Optimization Controls")
    ticker = st.text_input("Asset Ticker", "SPY")
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365*10))
    
    st.subheader("Layer 1: Patterns")
    z_val = st.slider("Z-Thresh (Constraint)", 0.60, 0.95, 0.85)
    e_val = st.slider("E-Thresh (Pressure)", 0.01, 0.10, 0.04)
    
    st.subheader("Layer 2: Survival")
    dd_val = st.slider("Max DD Target (%)", 5, 20, 10) / 100
    
    st.subheader("Layer 4: Consensus")
    smooth_val = st.slider("Smoothing Window", 1, 20, 8)

@st.cache_data
def run_simulation(symbol, start, z_t, e_t, dd_t, s_v):
    try:
        df_raw = yf.download(symbol, start=start, progress=False)
        
        # Guard against empty data (Fixes the IndexError)
        if df_raw.empty or len(df_raw) < 20:
            return None
            
        # Standardize columns for yfinance MultiIndex
        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = df_raw.columns.get_level_values(0)
            
        # 1. World Pattern
        df = WorldPatternLayer.extract_patterns(df_raw)
        
        body = EmbodimentLayer(dd_t)
        bridge = LogicalBridge(z_t, e_t)
        
        cash = 100000
        shares = cash / df['Close'].iloc[0]
        cash = 0
        peak = 100000
        
        nav_history = []
        raw_signals = []
        
        for i in range(len(df)):
            price = df['Close'].iloc[i]
            cur_nav = cash + (shares * price)
            peak = max(peak, cur_nav)
            
            vit, dd = body.get_vitality_state(cur_nav, peak)
            hedge_intent = bridge.decide(df['z_score'].iloc[i], df['entropy_integral'].iloc[i], vit)
            raw_signals.append(hedge_intent)
            
            # Layer 4: Smoothing
            if i >= s_v:
                consensus_hr = np.mean(raw_signals[-s_v:])
            else:
                consensus_hr = hedge_intent
                
            # Execution
            target_cash = cur_nav * consensus_hr
            if cash < target_cash:
                to_sell = (target_cash - cash) / price
                qty = min(shares, to_sell)
                shares -= qty
                cash += qty * price
            elif consensus_hr < 0.1 and cash > 0:
                shares += cash / price
                cash = 0
                
            nav_history.append(cash + shares * price)
            
        df['equity'] = nav_history
        df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
        df['bh_equity'] = (df['Close'] / df['Close'].iloc[0]) * 100000
        return df
    except Exception as e:
        st.error(f"Engine Error: {e}")
        return None

results = run_simulation(ticker, start_date, z_val, e_val, dd_val, smooth_val)

if results is not None:
    # Calculate Metrics
    yrs = (results.index[-1] - results.index[0]).days / 365.25
    cagr = (results['equity'].iloc[-1] / 100000)**(1/yrs) - 1
    bh_cagr = (results['bh_equity'].iloc[-1] / 100000)**(1/yrs) - 1

    col1, col2, col3 = st.columns(3)
    col1.metric("A7DO CAGR", f"{cagr*100:.2f}%", delta=f"{(cagr-bh_cagr)*100:.2f}% vs B&H")
    col2.metric("Max Drawdown", f"{results['drawdown'].max()*100:.2f}%", delta_color="inverse")
    col3.metric("Final Capital", f"${results['equity'].iloc[-1]:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=results.index, y=results['bh_equity'], name="Buy & Hold", line=dict(color="#475569", dash="dot")))
    fig.add_trace(go.Scatter(x=results.index, y=results['equity'], name="SLED Recovery", line=dict(color="#10b981", width=2.5)))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"No data found for ticker '{ticker}'. Please check the symbol and date range.")

