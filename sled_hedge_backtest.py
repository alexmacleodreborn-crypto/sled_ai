import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("SLED Hedge Engine Backtest")

# ----------------------------
# User Inputs
# ----------------------------
ticker = st.text_input("Ticker", "SPY")
start = st.date_input("Start Date", pd.to_datetime("2010-01-01"))
end = st.date_input("End Date", pd.to_datetime("today"))

# ----------------------------
# Load Data
# ----------------------------
data = yf.download(ticker, start=start, end=end)
data = data[['Close']].dropna()

# ----------------------------
# SLED Core Calculations
# ----------------------------

data['returns'] = data['Close'].pct_change().fillna(0)

# Sigma = scaled rolling volatility
data['sigma'] = data['returns'].rolling(5).std() * 100
data['sigma'] = data['sigma'].fillna(0)

# Z Constraint (compression proxy)
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

cash = 100000
shares = 0
peak = 100000

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
    else:
        hedge_ratio = 0

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
# Metrics
# ----------------------------

cagr = (data['equity'].iloc[-1] / 100000) ** (252 / len(data)) - 1
max_dd = max(data['drawdown'])
vol = data['equity'].pct_change().std() * np.sqrt(252)
sharpe = (cagr / vol) if vol > 0 else 0

# ----------------------------
# Dashboard
# ----------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Final Equity", f"${data['equity'].iloc[-1]:,.0f}")
col2.metric("CAGR", f"{cagr*100:.2f}%")
col3.metric("Max Drawdown", f"{max_dd*100:.2f}%")
col4.metric("Sharpe Ratio", f"{sharpe:.2f}")

st.subheader("Equity Curve")
st.line_chart(data[['equity']])

st.subheader("Hedge Ratio")
st.line_chart(data[['hedge_ratio']])

st.subheader("Price vs Entropy Integral")
st.line_chart(data[['Close', 'entropyIntegral']])