import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("SLED Hedge Engine — Robust Backtest")

# -------------------------------------------------
# SIDEBAR PARAMETERS
# -------------------------------------------------

st.sidebar.header("SLED Parameters")

decay_factor = st.sidebar.slider("Entropy Decay", 0.80, 0.99, 0.92, 0.01)
entropy_trigger = st.sidebar.slider("Entropy Trigger", 0.01, 0.20, 0.05, 0.01)
z_trigger = st.sidebar.slider("Z Threshold", 0.70, 0.95, 0.85, 0.01)
drawdown_limit = st.sidebar.slider("Drawdown Limit", 0.02, 0.20, 0.08, 0.01)

# -------------------------------------------------
# USER INPUT
# -------------------------------------------------

col1, col2, col3 = st.columns(3)

ticker = col1.text_input("Ticker", "SPY")
start = col2.date_input("Start Date", pd.to_datetime("2010-01-01"))
end = col3.date_input("End Date", pd.to_datetime("today"))

initial_capital = 100000

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

data = yf.download(ticker, start=start, end=end, progress=False)

if data.empty:
    st.error("No data returned.")
    st.stop()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

data = data[['Close']].dropna()

if len(data) < 60:
    st.warning("Not enough data.")
    st.stop()

# -------------------------------------------------
# CORE CALCULATIONS
# -------------------------------------------------

data['returns'] = data['Close'].pct_change().fillna(0)
data['sigma'] = data['returns'].rolling(5).std().fillna(0)

price_delta = data['Close'].diff().abs().fillna(0)
sigma_safe = data['sigma'] + 1e-8

data['z'] = 1 - (price_delta / (sigma_safe + 1))
data['z'] = data['z'].clip(0.01, 0.99)

# Entropy Integral
entropy = []
e = 0
for s in data['sigma']:
    e = e * decay_factor + s
    entropy.append(e)

data['entropyIntegral'] = entropy

# -------------------------------------------------
# PORTFOLIO SIMULATION FUNCTION
# -------------------------------------------------

def run_backtest(df):

    cash = initial_capital
    shares = 0
    peak = initial_capital

    equity_curve = []
    hedge_ratios = []
    drawdowns = []

    for i in range(len(df)):

        price = df['Close'].iloc[i]
        sigma = df['sigma'].iloc[i]
        z = df['z'].iloc[i]
        eInt = df['entropyIntegral'].iloc[i]

        total_equity = cash + shares * price
        peak = max(peak, total_equity)
        drawdown = (peak - total_equity) / peak

        defensive = False
        if eInt > entropy_trigger and z > z_trigger:
            defensive = True
        if drawdown > drawdown_limit:
            defensive = True

        hedge_ratio = 0
        if defensive:
            hedge_ratio = min(1, eInt * 10)

        target_cash = total_equity * hedge_ratio

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

    df = df.copy()
    df['equity'] = equity_curve
    df['hedge_ratio'] = hedge_ratios
    df['drawdown'] = drawdowns
    df['exposure'] = 1 - df['hedge_ratio']

    return df

# -------------------------------------------------
# WALK-FORWARD SPLIT
# -------------------------------------------------

split_index = int(len(data) * 0.7)

train = data.iloc[:split_index]
test = data.iloc[split_index:]

train_bt = run_backtest(train)
test_bt = run_backtest(test)

full_bt = run_backtest(data)

# -------------------------------------------------
# BUY & HOLD
# -------------------------------------------------

bh_shares = initial_capital / data['Close'].iloc[0]
data['buy_hold_equity'] = bh_shares * data['Close']

# -------------------------------------------------
# METRICS FUNCTION
# -------------------------------------------------

def calculate_metrics(df):

    years = (df.index[-1] - df.index[0]).days / 365.25
    final_equity = df['equity'].iloc[-1]

    cagr = (final_equity / initial_capital) ** (1 / years) - 1

    returns = df['equity'].pct_change().dropna()
    vol = returns.std() * np.sqrt(252)
    sharpe = (returns.mean() * 252) / vol if vol > 0 else 0

    max_dd = df['drawdown'].max()

    return final_equity, cagr, sharpe, max_dd

# Calculate metrics
train_metrics = calculate_metrics(train_bt)
test_metrics = calculate_metrics(test_bt)
full_metrics = calculate_metrics(full_bt)

bh_years = (data.index[-1] - data.index[0]).days / 365.25
bh_final = data['buy_hold_equity'].iloc[-1]
bh_cagr = (bh_final / initial_capital) ** (1 / bh_years) - 1

# -------------------------------------------------
# DASHBOARD OUTPUT
# -------------------------------------------------

st.header("Full Sample Performance")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Equity", f"${full_metrics[0]:,.0f}")
c2.metric("CAGR", f"{full_metrics[1]*100:.2f}%")
c3.metric("Sharpe", f"{full_metrics[2]:.2f}")
c4.metric("Max Drawdown", f"{full_metrics[3]*100:.2f}%")

st.metric("Buy & Hold CAGR", f"{bh_cagr*100:.2f}%")

st.header("Walk-Forward Validation")

wf1, wf2 = st.columns(2)

wf1.subheader("In-Sample (70%)")
wf1.metric("CAGR", f"{train_metrics[1]*100:.2f}%")
wf1.metric("Sharpe", f"{train_metrics[2]:.2f}")
wf1.metric("Max DD", f"{train_metrics[3]*100:.2f}%")

wf2.subheader("Out-of-Sample (30%)")
wf2.metric("CAGR", f"{test_metrics[1]*100:.2f}%")
wf2.metric("Sharpe", f"{test_metrics[2]:.2f}")
wf2.metric("Max DD", f"{test_metrics[3]*100:.2f}%")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------

st.subheader("Equity Curve vs Buy & Hold")
st.line_chart(pd.concat([full_bt['equity'], data['buy_hold_equity']], axis=1))

st.subheader("Hedge Ratio")
st.line_chart(full_bt[['hedge_ratio']])

st.subheader("Exposure")
st.line_chart(full_bt[['exposure']])

st.subheader("Entropy Integral")
st.line_chart(full_bt[['entropyIntegral']])