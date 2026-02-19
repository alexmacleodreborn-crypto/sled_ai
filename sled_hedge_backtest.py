import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("SLED Hedge Engine — Backtest")

# ----------------------------
# User Inputs
# ----------------------------
colA, colB, colC = st.columns(3)

ticker = colA.text_input("Ticker", "SPY")
start = colB.date_input("Start Date", pd.to_datetime("2010-01-01"))
end = colC.date_input("End Date", pd.to_datetime("today"))

initial_capital = 100000

# ----------------------------
# Load Data
# ----------------------------
data = yf.download(ticker, start=start, end=end, progress=False)

if data.empty:
    st.error("No data returned. Check ticker or date range.")
    st.stop()

data = data[['Close']].dropna()

# ----------------------------
# SLED Core Calculations
# ----------------------------

data['returns'] = data['Close'].pct_change().fillna(0)

# Rolling volatility proxy
data['sigma'] = data['returns'].rolling(5).std() * 100
data['sigma'] = data['sigma'].fillna(0)

# Constraint proxy
price_delta = data['Close'].diff().abs().fillna(0)
data['z'] = 1 - (price_delta / (data['sigma'] + 1))
data['z'] = data['z'].clip(0.01, 0.99)

# Entropy Integral (memory)
entropy = []
e = 0
for s in data['sigma']:
    e = e * 0.92 + s
    entropy.append(e)

data['entropyIntegral'] = entropy

# ----------------------------
# Portfolio Simulation
# ----------------------------

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

    # Defensive regime
    defensive = False
    if eInt > 5 and z > 0.82:
        defensive = True
    if drawdown > 0.08:
        defensive = True

    # Hedge scaling
    hedge_ratio = 0
    if defensive:
        hedge_ratio = min(1, (eInt - 5) / 10)

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

# ----------------------------
# Buy & Hold Benchmark
# ----------------------------

bh_shares = initial_capital / data['Close'].iloc[0]
data['buy_hold_equity'] = bh_shares * data['Close']

# ----------------------------
# Performance Metrics
# ----------------------------

if len(data) > 1:

    years = (data.index[-1] - data.index[0]).days / 365.25

    final_equity = data['equity'].iloc[-1]
    bh_final = data['buy_hold_equity'].iloc[-1]

    cagr = (final_equity / initial_capital) ** (1 / years) - 1
    bh_cagr = (bh_final / initial_capital) ** (1 / years) - 1

    max_dd = data['drawdown'].max()

    returns = data['equity'].pct_change().dropna()
    vol = returns.std() * np.sqrt(252)
    sharpe = (returns.mean() * 252) / vol if vol > 0 else 0

    # ----------------------------
    # Dashboard
    # ----------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Final Equity", f"${final_equity:,.0f}")
    col2.metric("CAGR", f"{cagr*100:.2f}%")
    col3.metric("Buy & Hold CAGR", f"{bh_cagr*100:.2f}%")
    col4.metric("Max Drawdown", f"{max_dd*100:.2f}%")
    col5.metric("Sharpe Ratio", f"{sharpe:.2f}")

else:
    st.warning("Not enough data to calculate metrics.")
    st.stop()

# ----------------------------
# Charts
# ----------------------------

st.subheader("Equity Curve vs Buy & Hold")
st.line_chart(data[['equity', 'buy_hold_equity']])

st.subheader("Hedge Ratio Over Time")
st.line_chart(data[['hedge_ratio']])

st.subheader("Price vs Entropy Integral")
st.line_chart(data[['Close', 'entropyIntegral']])