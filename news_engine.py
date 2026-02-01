"""
news_engine.py
--------------
Persistent news profiling using NewsData.io
"""

import requests
import streamlit as st
from datetime import datetime

NEWS_ENDPOINT = "https://newsdata.io/api/1/news"


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

    params = {
        "apikey": api_key,
        "q": ticker,
        "language": "en",
    }

    try:
        r = requests.get(NEWS_ENDPOINT, params=params, timeout=10)
        data = r.json()
    except Exception:
        return []

    articles = []
    for a in data.get("results", [])[:max_items]:
        text = f"{a.get('title','')} {a.get('description','')}"
        articles.append({
            "ticker": ticker,
            "title": a.get("title",""),
            "source": a.get("source_id",""),
            "sentiment": classify_sentiment(text),
            "published": a.get("pubDate",""),
        })

    return articles


def build_news_profile(ticker: str):
    """
    Returns a persistent profile summarising recent news.
    """
    articles = fetch_newsdata_articles(ticker)

    if not articles:
        return {
            "Ticker": ticker,
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
        "News_Count": len(articles),
        "Sentiment": net,
        "Narrative_Pressure": round(pressure, 3),
        "Last_Update": datetime.utcnow().isoformat(),
        "Articles": articles,
    }