import pandas as pd
import numpy as np
from scipy.stats import entropy
import yfinance as yf

# ---------------- NEWS FILTER ----------------

NEWS_KEYWORDS = [
    "earnings","revenue","profit","guidance",
    "acquisition","merger","divest","sale",
    "regulation","lawsuit","investigation",
    "ceo","cfo","board","executive"
]

NEGATIVE_WORDS = {
    "miss","cut","downgrade","loss","decline",
    "investigation","lawsuit","fine","probe",
    "recall","drop","delay","weak"
}

POSITIVE_WORDS = {
    "beat","growth","upgrade","record",
    "strong","expand","increase","approval"
}

def classify_news_sentiment(text: str):
    t = text.lower()
    neg = sum(w in t for w in NEGATIVE_WORDS)
    pos = sum(w in t for w in POSITIVE_WORDS)
    if neg > pos: return "NEGATIVE"
    if pos > neg: return "POSITIVE"
    return "NEUTRAL"

def safe_news(ticker: str, limit=8):
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        return []
    out = []
    for n in raw[:limit]:
        text = f"{n.get('title','')} {n.get('summary','')}"
        if not any(k in text.lower() for k in NEWS_KEYWORDS):
            continue
        out.append({
            "ticker": ticker,
            "title": n.get("title",""),
            "sentiment": classify_news_sentiment(text)
        })
    return out

def apply_news_filter(signal, news):
    if signal == "WAIT":
        return "WAIT", "No signal"
    if not news:
        return signal, "No relevant news"
    sentiments = {n["sentiment"] for n in news}
    if signal == "BUY" and "NEGATIVE" in sentiments:
        return "WAIT", "Cancelled by negative news"
    if signal == "SELL" and "POSITIVE" in sentiments:
        return "WAIT", "Cancelled by positive news"
    return signal, "News confirms signal"

# ---------------- DATA ----------------

def safe_history(ticker, period="6mo"):
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df is None or df.empty or "Close" not in df.columns:
            return None
        return df
    except Exception:
        return None

# ---------------- SLED ENGINE ----------------

class SLEDEngine:
    def __init__(self, window=20, lookback=100, entropy_bins=10):
        self.window = window
        self.lookback = lookback
        self.entropy_bins = entropy_bins

    def calculate(self, df):
        close = df["Close"]
        df["Log_Return"] = np.log(close / close.shift(1)).fillna(0)
        df["Rolling_Std"] = df["Log_Return"].rolling(self.window).std()

        rmin = df["Rolling_Std"].rolling(self.lookback).min()
        rmax = df["Rolling_Std"].rolling(self.lookback).max()
        denom = rmax - rmin

        df["Z_Trap"] = 1 - np.where(denom == 0, 0, (df["Rolling_Std"] - rmin) / denom)

        def ent(s):
            h,_ = np.histogram(s, bins=self.entropy_bins)
            if h.sum() == 0: return 0
            p = h/h.sum()
            return entropy(p[p>0], base=2)

        df["Sigma"] = df["Log_Return"].rolling(self.window).apply(ent)
        df["Gate"] = (1 - df["Z_Trap"]) * df["Sigma"]

        low = close.rolling(50).min()
        high = close.rolling(50).max()
        df["Price_Loc"] = np.where(high-low==0,0.5,(close-low)/(high-low))

        ent_th = df["Sigma"].rolling(200).quantile(0.85)
        phase0 = (df["Z_Trap"]>0.75) & (df["Sigma"]>ent_th)

        df["Signal_Buy"] = (phase0 & (df["Price_Loc"]<0.4)).astype(int)
        df["Signal_Sell"] = (phase0 & (df["Price_Loc"]>0.6)).astype(int)

        df["RiseScore_14d"] = df["Gate"]*0.6 + df["Sigma"]*0.3 - df["Z_Trap"]*0.4
        return df

    def summarize(self, df):
        r = df.iloc[-1]
        signal = "WAIT"
        if r.Signal_Buy: signal="BUY"
        if r.Signal_Sell: signal="SELL"

        bull = (signal!="WAIT") and r.Gate>1.6 and r.Z_Trap<0.85

        return {
            "Price": round(float(r.Close),2),
            "Signal": signal,
            "Gate": round(float(r.Gate),3),
            "Z_Trap": round(float(r.Z_Trap),3),
            "Sigma": round(float(r.Sigma),3),
            "RiseScore_14d": round(float(r.RiseScore_14d),3),
            "Bullseye": bull
        }