"""
news_engine.py
--------------
Company-aware news profiling using NewsData.io
Restores rich news flow (Yahoo-like) but cleaner
"""

import requests
import streamlit as st
from datetime import datetime

NEWS_ENDPOINT = "https://newsdata.io/api/1/news"

# ----------------------------------
# TICKER → COMPANY NAME MAP
# ----------------------------------
COMPANY_MAP = {
    "NVDA": "Nvidia",
    "MSFT": "Microsoft",
    "AAPL": "Apple",
    "META": "Meta",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "AMD": "AMD",
    "INTC": "Intel",
    "TSM": "TSMC",
    "ASML": "ASML",
    "ARM": "Arm Holdings",
    "TSLA": "Tesla",
    "PLTR": "Palantir",
    "COIN": "Coinbase",
    "SNOW": "Snowflake",
    "RIVN": "Rivian",
    "XOM": "Exxon",
    "CVX": "Chevron",
    "OXY": "Occidental Petroleum",
    "SLB": "Schlumberger",
    "JPM": "JPMorgan",
    "GS": "Goldman Sachs",
    "BAC": "Bank of America",
    "MS": "Morgan Stanley",
}

POSITIVE_TERMS = {
    "growth","record","expansion","approval","beat",
    "upgrade","strong","profit","surge","acquire"
}

NEGATIVE_TERMS = {
    "loss","decline","cut","downgrade","lawsuit",
    "probe","delay","miss","recall","weak"
}


def classify_sentiment(text: str) -> str:
    t = (text or "").lower()
    pos = sum(w in t for w in POSITIVE_TERMS)
    neg = sum(w in t for w in NEGATIVE_TERMS)
    if pos > neg:
        return "POSITIVE"
    if neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


def fetch_newsdata_articles(ticker: str, max_items: int = 10):
    api_key = st.secrets.get("NEWSDATA_API_KEY")
    if not api_key:
        return []

    company = COMPANY_MAP.get(ticker, ticker)
    query = f"{company} OR {ticker}"

    params = {
        "apikey": api_key,
        "q": query,
        "category": "business",
        "language": "en",
    }

    try:
        r = requests.get(NEWS_ENDPOINT, params=params, timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()
    except Exception:
        return []

    results = data.get("results")
    if not isinstance(results, list):
        return []

    articles = []
    for a in results[:max_items]:
        text = f"{a.get('title','')} {a.get('description','')}"
        articles.append({
            "ticker": ticker,
            "company": company,
            "title": a.get("title",""),
            "source": a.get("source_id",""),
            "sentiment": classify_sentiment(text),
            "published": a.get("pubDate",""),
        })

    return articles


def build_news_profile(ticker: str):
    """
    Builds a persistent, high-signal news profile.
    """
    articles = fetch_newsdata_articles(ticker)

    if not articles:
        return {
            "Ticker": ticker,
            "Company": COMPANY_MAP.get(ticker, ticker),
            "News_Count": 0,
            "Sentiment": "NONE",
            "Narrative_Pressure": 0.0,
            "Last_Update": datetime.utcnow().isoformat(),
            "Articles": [],
        }

    pos = sum(a["sentiment"] == "POSITIVE" for a in articles)
    neg = sum(a["sentiment"] == "NEGATIVE" for a in articles)

    pressure = (pos - neg) / max(1, len(articles))

    if pressure > 0.25:
        net = "POSITIVE"
    elif pressure < -0.25:
        net = "NEGATIVE"
    else:
        net = "MIXED"

    return {
        "Ticker": ticker,
        "Company": COMPANY_MAP.get(ticker, ticker),
        "News_Count": len(articles),
        "Sentiment": net,
        "Narrative_Pressure": round(pressure, 3),
        "Last_Update": datetime.utcnow().isoformat(),
        "Articles": articles,
    }