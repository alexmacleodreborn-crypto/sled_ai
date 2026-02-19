import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="SLED Pro Backtester")

st.title("SLED Hedge Engine — Robust Backtest")
st.markdown("---")

# -------------------------------------------------
# 1. PARAMETERS & INPUTS
# -------------------------------------------------
with st.sidebar:
    st.header("1. Asset & Timeline")
    ticker = st.text_input("Ticker", "SPY")
    start_date = st.date_input("Start Date", pd.to_datetime("2010-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))
    
    st.header("2. SLED Tuning")
    z_limit = st.slider("Z-Threshold (Constraint)", 0.70, 0.98, 0.85)
    e_limit = st.slider("E-Integral Threshold", 0.01, 0.20, 0.05)
    decay = st.slider("Integral Decay", 0.80, 0.99, 0.92)
    
    st.header("3. Risk Management")
    dd_limit = st.slider("Max DD Governor (%)", 5, 20, 8) / 100
    oos_split = st.slider("Out-of-Sample Split (%)", 50, 90, 70) / 100

# -------------------------------------------------
# 2. DATA ENGINE
# -------------------------------------------------
@st.cache_data
def load_and_process(symbol, start, end):
    df = yf.download(symbol, start=start, end=end, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[['Close']].copy()
    
    # Physics Metrics
    df['returns'] = df['Close'].pct_change().fillna(0)
    df['sigma'] = df['returns'].rolling(5).std().fillna(0)
    
    # Z (Constraint)
    price_delta = df['Close'].diff().abs().fillna(0)
    sigma_norm = df['sigma'] * df['Close'] + 1e-6
    df['z'] = (1 - (price_delta / sigma_norm)).clip(0.01, 0.99)
    
    # Entropy Integral
    entropy = []
    e = 0
    for s in df['sigma']:
        e = e * decay + s
        entropy.append(e)
    df['e_int'] = entropy
    
    return df

data = load_and_process(ticker, start_date, end_date)

# -------------------------------------------------
# 3. BACKTEST ENGINE
# -------------------------------------------------
def backtest(df, initial_capital=100000):
    cash = initial_capital
    shares = 0
    peak = initial_capital
    
    equity_curve = []
    hedge_ratios = []
    
    for i in range(len(df)):
        price = df['Close'].iloc[i]
        z = df['z'].iloc[i]
        e_int = df['e_int'].iloc[i]
        
        current_val = cash + (shares * price)
        peak = max(peak, current_val)
        drawdown = (peak - current_val) / peak
        
        # SLED Logic
        is_trap = (z > z_limit and e_int > e_limit)
        is_breach = (drawdown > dd_limit)
        
        hedge_ratio = 0
        if is_breach: hedge_ratio = 1.0
        elif is_trap: hedge_ratio = min(1.0, (e_int / e_limit) - 0.5)

        # Execution
        target_cash = current_val * max(0, hedge_ratio)
        if target_cash > cash:
            to_sell = (target_cash - cash) / price
            sold = min(shares, to_sell)
            shares -= sold
            cash += sold * price
        elif target_cash < cash and not is_trap and not is_breach:
            # Re-entry: Only when clear of traps
            shares += cash / price
            cash = 0
            
        equity_curve.append(cash + shares * price)
        hedge_ratios.append(hedge_ratio)
        
    df['equity'] = equity_curve
    df['hedge_ratio'] = hedge_ratios
    df['drawdown'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
    return df

# Split Logic
split_idx = int(len(data) * oos_split)
is_df = data.iloc[:split_idx].copy()
oos_df = data.iloc[split_idx:].copy()

is_results = backtest(is_df)
oos_results = backtest(oos_df, initial_capital=is_results['equity'].iloc[-1])
full_results = pd.concat([is_results, oos_results])

# -------------------------------------------------
# 4. METRICS & VISUALS
# -------------------------------------------------
def get_metrics(df):
    years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = (df['equity'].iloc[-1] / df['equity'].iloc[0])**(1/years) - 1
    mdd = df['drawdown'].max()
    ret = df['equity'].pct_change().dropna()
    sharpe = (ret.mean() * 252) / (ret.std() * np.sqrt(252)) if ret.std() > 0 else 0
    return cagr, mdd, sharpe

# Performance Display
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Full Sample")
    c, m, s = get_metrics(full_results)
    st.metric("Final Equity", f"${full_results['equity'].iloc[-1]:,.0f}")
    st.metric("CAGR", f"{c*100:.2f}%")
    st.metric("Max DD", f"{m*100:.2f}%")

with c2:
    st.subheader("In-Sample (Train)")
    c, m, s = get_metrics(is_results)
    st.write(f"CAGR: {c*100:.2f}%")
    st.write(f"Sharpe: {s:.2f}")

with c3:
    st.subheader("Out-of-Sample (Test)")
    c, m, s = get_metrics(oos_results)
    st.write(f"CAGR: {c*100:.2f}%")
    st.write(f"Sharpe: {s:.2f}")

# Charts
st.subheader("Equity Curve vs Buy & Hold")
bh_equity = (full_results['Close'] / full_results['Close'].iloc[0]) * 100000
fig = go.Figure()
fig.add_trace(go.Scatter(x=full_results.index, y=full_results['equity'], name='SLED Engine', line=dict(color='#10b981')))
fig.add_trace(go.Scatter(x=full_results.index, y=bh_equity, name='Buy & Hold', line=dict(color='#475569', dash='dot')))
fig.add_vline(x=data.index[split_idx], line_dash="dash", line_color="white", annotation_text="OOS Split")
fig.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Hedge Exposure (0 = Fully Invested, 1 = Cash)")
st.area_chart(full_results['hedge_ratio'])

