import pandas as pd
import numpy as np
from scipy.stats import entropy
import yfinance as yf

# ==================================================
# NEWS FILTER (RELEVANCE + SENTIMENT)
# ==================================================

NEWS_KEYWORDS = [
    "earnings", "revenue", "profit", "guidance",
    "acquisition", "merger", "divest", "sale",
    "regulation", "lawsuit", "investigation",
    "ceo", "cfo", "board", "executive"
]

NEGATIVE_WORDS = {
    "miss", "cut", "downgrade", "loss", "decline",
    "investigation", "lawsuit", "fine", "probe",
    "recall", "drop", "delay", "weak"
}

POSITIVE_WORDS = {
    "beat", "growth", "upgrade", "record",
    "strong", "expand", "increase", "approval"
}


def classify_news_sentiment(text: str) -> str:
    t = (text or "").lower()
    neg = sum(w in t for w in NEGATIVE_WORDS)
    pos = sum(w in t for w in POSITIVE_WORDS)
    if neg > pos:
        return "NEGATIVE"
    if pos > neg:
        return "POSITIVE"
    return "NEUTRAL"


def safe_news(ticker: str, limit: int = 8):
    """
    Returns ONLY relevant news items.
    News can CONFIRM or CANCEL signals, never create them.
    """
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        return []

    relevant = []
    for n in raw[:limit]:
        text = f"{n.get('title','')} {n.get('summary','')}"
        if not any(k in text.lower() for k in NEWS_KEYWORDS):
            continue

        relevant.append({
            "ticker": ticker,
            "title": n.get("title", ""),
            "sentiment": classify_news_sentiment(text)
        })

    return relevant


def apply_news_filter(signal: str, news_items: list):
    """
    Enforces: news may cancel or confirm, never create.
    """
    if signal == "WAIT":
        return "WAIT", "No SLED signal"

    if not news_items:
        return signal, "No relevant news"

    sentiments = {n["sentiment"] for n in news_items}

    if signal == "BUY" and "NEGATIVE" in sentiments:
        return "WAIT", "Cancelled by negative news"

    if signal == "SELL" and "POSITIVE" in sentiments:
        return "WAIT", "Cancelled by positive news"

    return signal, "News confirms signal"


# ==================================================
# SAFE PRICE HISTORY
# ==================================================

def safe_history(ticker: str, period: str = "6mo"):
    try:
        df = yf.download(
            ticker,
            period=period,
            progress=False,
            auto_adjust=True
        )
        if df is None or df.empty:
            return None
        if "Close" not in df.columns:
            return None
        return df
    except Exception:
        return None


# ==================================================
# SLED ENGINE
# ==================================================

class SLEDEngine:
    def __init__(self, window: int = 20, lookback: int = 100, entropy_bins: int = 10):
        self.window = window
        self.lookback = lookback
        self.entropy_bins = entropy_bins

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["Close"]

        # 1) Velocity
        df["Log_Return"] = np.log(close / close.shift(1)).fillna(0)

        # 2) Trap (Z)
        df["Rolling_Std"] = df["Log_Return"].rolling(self.window).std()
        rmin = df["Rolling_Std"].rolling(self.lookback).min()
        rmax = df["Rolling_Std"].rolling(self.lookback).max()
        denom = rmax - rmin

        df["Z_Trap"] = 1 - np.where(
            denom == 0,
            0,
            (df["Rolling_Std"] - rmin) / denom
        )

        # 3) Flow (Sigma)
        def entropy_calc(series):
            h, _ = np.histogram(series, bins=self.entropy_bins)
            if h.sum() == 0:
                return 0.0
            p = h / h.sum()
            p = p[p > 0]
            return entropy(p, base=2)

        df["Sigma"] = (
            df["Log_Return"]
            .rolling(self.window)
            .apply(entropy_calc)
        )

        # 4) Gate
        df["Gate"] = (1 - df["Z_Trap"]) * df["Sigma"]

        # 5) Relative Price Location
        low = close.rolling(50).min()
        high = close.rolling(50).max()
        df["Price_Loc"] = np.where(
            high - low == 0,
            0.5,
            (close - low) / (high - low)
        )

        # 6) Phase-0 Signals
        ent_thresh = df["Sigma"].rolling(200).quantile(0.85)
        phase0 = (df["Z_Trap"] > 0.75) & (df["Sigma"] > ent_thresh)

        df["Signal_Buy"] = (phase0 & (df["Price_Loc"] < 0.4)).astype(int)
        df["Signal_Sell"] = (phase0 & (df["Price_Loc"] > 0.6)).astype(int)

        # 7) Forward asymmetry proxy
        df["RiseScore_14d"] = (
            df["Gate"] * 0.6 +
            df["Sigma"] * 0.3 -
            df["Z_Trap"] * 0.4
        )

        return df

    def summarize(self, df: pd.DataFrame) -> dict:
        """
        SAFE summarize — no Pandas truth ambiguity.
        """
        r = df.iloc[-1]

        buy = int(r.get("Signal_Buy", 0))
        sell = int(r.get("Signal_Sell", 0))

        if buy == 1:
            signal = "BUY"
        elif sell == 1:
            signal = "SELL"
        else:
            signal = "WAIT"

        bullseye = (
            signal != "WAIT"
            and float(r["Gate"]) > 1.6
            and float(r["Z_Trap"]) < 0.85
        )

        return {
            "Price": round(float(r["Close"]), 2),
            "Signal": signal,
            "Gate": round(float(r["Gate"]), 4),
            "Z_Trap": round(float(r["Z_Trap"]), 4),
            "Sigma": round(float(r["Sigma"]), 4),
            "RiseScore_14d": round(float(r["RiseScore_14d"]), 4),
            "Bullseye": bool(bullseye),
        }