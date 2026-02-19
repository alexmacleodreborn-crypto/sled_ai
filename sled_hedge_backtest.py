import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Graceful Plotly Import
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.set_page_config(layout="wide", page_title="SLED Backtest V6")

st.title("🛡️ SLED Hedge Engine — Robust Backtest V6")
st.markdown("### Resolving the 'Stuck in Cash' Bias")

# -------------------------------------------------
# 1. SIDEBAR CONFIGURATION
# -------------------------------------------------
with st.sidebar:
    st.header("Asset & Timeline")
    ticker = st.text_input("Ticker", "SPY")
    start_date = st.date_input("Start Date", pd.to_datetime("2010-01-01"))
    
    st.divider()
    st.header("SLED Physics Tuning")
    z_limit = st.slider("Z-Threshold (Compression)", 0.60, 0.98, 0.85)
    e_limit = st.slider("Entropy Limit (Threshold)", 0.01, 0.15, 0.045)
    decay = st.slider("Integral Memory (Decay)", 0.80, 0.99, 0.92)
    
    st.divider()
    st.header("Risk & Validation")
    dd_limit = st.slider("Drawdown Governor (%)", 3, 20, 10) / 100
    oos_split = st.slider("In-Sample Split (%)", 50, 90, 70) / 100

# -------------------------------------------------
# 2. DATA PROCESSING
# -------------------------------------------------
@st.cache_data
def load_and_calculate(symbol, start):
    df = yf.download(symbol, start=start, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df[['Close']].copy()
    df['returns'] = df['Close'].pct_change().fillna(0)
    
    # Entropy Proxy: 5-day rolling volatility
    df['sigma'] = df['returns'].rolling(5).std().fillna(0)
    
    # Z Proxy: Structural Constraint
    # We normalize delta by price-scaled sigma to keep Z consistent across price regimes
    price_delta = df['Close'].diff().abs().fillna(0)
    sigma_scaled = (df['sigma'] * df['Close']) + 1e-6
    df['z'] = (1 - (price_delta / sigma_scaled)).clip(0.01, 0.99)
    
    # Entropy Integral: Pressure Memory
    e_ints = []
    e_acc = 0
    for s in df['sigma']:
        e_acc = e_acc * decay + s
        e_ints.append(e_acc)
    df['e_int'] = e_ints
    
    return df

data = load_and_calculate(ticker, start_date)

# -------------------------------------------------
# 3. HEDGE SIMULATION ENGINE
# -------------------------------------------------
def run_simulation(df, initial_equity=100000):
    cash = initial_equity
    shares = 0
    peak = initial_equity
    
    history_equity = []
    history_hedge = []
    
    # Start fully invested
    shares = cash / df['Close'].iloc[0]
    cash = 0
    
    for i in range(len(df)):
        price = df['Close'].iloc[i]
        z = df['z'].iloc[i]
        e_int = df['e_int'].iloc[i]
        
        current_nav = cash + (shares * price)
        peak = max(peak, current_nav)
        drawdown = (peak - current_nav) / peak
        
        # LOGIC: The Entropic Gate
        # Trap detected if both Constraint (Z) and Pressure (E) are high
        is_trap = (z > z_limit and e_int > e_limit)
        is_breach = (drawdown > dd_limit)
        
        # PROPORTIONAL HEDGE
        target_h = 0
        if is_breach:
            target_h = 1.0 # Immediate liquidation on hard DD breach
        elif is_trap:
            # Scale hedge: how far are we past the limit?
            target_h = min(1.0, (e_int / e_limit) - 0.5)
            target_h = max(0.0, target_h)

        # REBALANCING
        target_cash_val = current_nav * target_h
        
        if target_h > 0:
            # Hedging (Selling)
            if cash < target_cash_val:
                to_sell = (target_cash_val - cash) / price
                shares_sold = min(shares, to_sell)
                shares -= shares_sold
                cash += shares_sold * price
        else:
            # Re-entry (Buying)
            # CRITICAL: Re-enter only when trap is cleared (E_Int drops)
            if cash > 0 and e_int < (e_limit * 0.8): 
                shares += cash / price
                cash = 0
        
        nav_at_end = cash + (shares * price)
        history_equity.append(nav_at_end)
        history_hedge.append(target_h)
        
    df['equity'] = history_equity
    df['hedge_ratio'] = history_hedge
    df['dd_curve'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    return df

# Split and Run
split_idx = int(len(data) * oos_split)
is_data = run_simulation(data.iloc[:split_idx].copy())
oos_data = run_simulation(data.iloc[split_idx:].copy(), initial_equity=is_data['equity'].iloc[-1])
full_data = pd.concat([is_data, oos_data])

# -------------------------------------------------
# 4. ANALYTICS & DASHBOARD
# -------------------------------------------------
def metrics_block(df, title):
    years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = (df['equity'].iloc[-1] / df['equity'].iloc[0])**(1/years) - 1
    mdd = df['dd_curve'].max()
    st.metric(title, f"{cagr*100:.2f}% CAGR", f"{mdd*100:.2f}% MaxDD", delta_color="inverse")

c1, c2, c3 = st.columns(3)
with c1: metrics_block(full_data, "Full Backtest")
with c2: metrics_block(is_data, "In-Sample")
with c3: metrics_block(oos_data, "Out-of-Sample")

# CHARTING
if HAS_PLOTLY:
    fig = go.Figure()
    # Benchmark
    bh_eq = (full_data['Close'] / full_data['Close'].iloc[0]) * 100000
    fig.add_trace(go.Scatter(x=full_data.index, y=bh_eq, name="Buy & Hold", line=dict(color="#475569", dash="dot")))
    # SLED
    fig.add_trace(go.Scatter(x=full_data.index, y=full_data['equity'], name="SLED Engine", line=dict(color="#10b981", width=2)))
    
    # Fix for the add_vline error: Use string representation of the timestamp
    split_date_str = data.index[split_idx].strftime('%Y-%m-%d')
    fig.add_vline(x=split_date_str, line_dash="dash", line_color="white", opacity=0.5)
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.line_chart(full_data[['equity']])

st.subheader("System State: Hedge Ratio & Entropy")
col_h, col_e = st.columns(2)
col_h.area_chart(full_data['hedge_ratio'])
col_e.line_chart(full_data['e_int'])

st.info("💡 V6 Update: Re-entry is now 'sticky'. It waits for the Entropy Integral to drop 20% below the limit before buying back in, preventing 'chopping' in volatile regimes.")

