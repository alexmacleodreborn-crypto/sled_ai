import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("SLED Hedge Engine — Backtest")

# -------------------------------------------------
# USER INPUT
# -------------------------------------------------

col1, col2, col3 = st.columns(3)

ticker = col1.text_input("Ticker", "SPY")
start = col2.date_input("Start Date", pd.to_datetime("2010-01-01"))
end = col3.date_input("End Date", pd.to_datetime("today"))

initial_capital = 100000

# -------------------------------------------------
# LOAD DATA (Robust Version)
# -------------------------------------------------

data = yf.download(ticker, start=start, end=end, progress=False)

if data.empty:
    st.error("No data returned. Check ticker or date range.")
    st.stop()

# Flatten multi-index columns if needed
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if 'Close' not in data.columns:
    st.error("Close column not found in dataset.")
    st.stop()

data = data[['Close']].copy()
data = data.dropna()

if len(data) < 30:
    st.warning("Not enough historical data for backtest.")
    st.stop()

# -------------------------------------------------
# SLED CORE CALCULATIONS
# -------------------------------------------------

# Returns
data['returns'] = data['Close'].pct_change().fillna(0)

# Rolling volatility (sigma)
data['sigma'] = data['returns'].rolling(window=5).std().fillna(0)

# Price delta
price_delta = data['Close'].diff().abs().fillna(0)

# Safe sigma
sigma_safe = data['sigma'] + 1e-8

# Constraint proxy (Z)
data['z'] = 1 - (price_delta / (sigma_safe + 1))
data['z'] = data['z'].clip(0.01, 0.99)

# Entropy integral (memory)
entropy = []
e = 0
for s in data['sigma']:
    e = e * 0.92 + s
    entropy.append(e)

data['entropyIntegral'] = entropy

# -------------------------------------------------
# PORTFOLIO SIMULATION
# -------------------------------------------------

cash = initial_capital
shares = 0
peak = initial_capital

equity_curve = []
hedge_ratios = []
drawdowns = []

for i in range(len(data)):

    price = data['Close'].iloc[i]
    sigma = data['sigma'].iloc[i]
    z = data['z'].iloc[i]
    eInt = data['entropyIntegral'].iloc[i]

    total_equity = cash + shares * price
    peak = max(peak, total_equity)
    drawdown = (peak - total_equity) / peak

    # Defensive regime trigger
    defensive = False
    if eInt > 0.05 and z > 0.85:
        defensive = True
    if drawdown > 0.08:
        defensive = True

    hedge_ratio = 0
    if defensive:
        hedge_ratio = min(1, eInt * 10)

    target_cash = total_equity * hedge_ratio

    # Adjust exposure
    if hedge_ratio > 0:
        if cash < target_cash:
            need_sell = (target_cash - cash) / price
            sell = min(shares, need_sell)
            shares -= sell
            cash += sell * price
    else:
        if cash > 0:
            shares += cash / price
            cash = 0

    total_equity = cash + shares * price

    equity_curve.append(total_equity)
    hedge_ratios.append(hedge_ratio)
    drawdowns.append(drawdown)

data['equity'] = equity_curve
data['hedge_ratio'] = hedge_ratios
data['drawdown'] = drawdowns

# -------------------------------------------------
# BUY & HOLD BENCHMARK
# -------------------------------------------------

bh_shares = initial_capital / data['Close'].iloc[0]
data['buy_hold_equity'] = bh_shares * data['Close']

# -------------------------------------------------
# PERFORMANCE METRICS
# -------------------------------------------------

years = (data.index[-1] - data.index[0]).days / 365.25

final_equity = data['equity'].iloc[-1]
bh_final = data['buy_hold_equity'].iloc[-1]

cagr = (final_equity / initial_capital) ** (1 / years) - 1
bh_cagr = (bh_final / initial_capital) ** (1 / years) - 1

max_dd = data['drawdown'].max()

returns = data['equity'].pct_change().dropna()
vol = returns.std() * np.sqrt(252)
sharpe = (returns.mean() * 252) / vol if vol > 0 else 0

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric("Final Equity", f"${final_equity:,.0f}")
m2.metric("CAGR", f"{cagr*100:.2f}%")
m3.metric("Buy & Hold CAGR", f"{bh_cagr*100:.2f}%")
m4.metric("Max Drawdown", f"{max_dd*100:.2f}%")
m5.metric("Sharpe Ratio", f"{sharpe:.2f}")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------

st.subheader("Equity vs Buy & Hold")
st.line_chart(data[['equity', 'buy_hold_equity']])

st.subheader("Hedge Ratio Over Time")
st.line_chart(data[['hedge_ratio']])

st.subheader("Price vs Entropy Integral")
st.line_chart(data[['Close', 'entropyIntegral']])