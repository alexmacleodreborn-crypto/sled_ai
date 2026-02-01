"""
news_engine.py
--------------
Company-anchored news profiling for in-house guests
"""

import requests
import streamlit as st
from datetime import datetime
import re

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
    "AMD": "Advanced Micro Devices",
    "INTC": "Intel",
    "TSM": "TSMC",
    "ASML": "ASML",
    "ARM": "Arm Holdings",
    "TSLA": "Tesla",
    "PLTR": "Palantir",
    "COIN": "Coinbase",
}

# ----------------------------------
# KEYWORD DICTIONARIES
# ----------------------------------
EVENT_KEYWORDS = {
    "earnings": "EARNINGS",
    "revenue": "EARNINGS",
    "guidance": "GUIDANCE",
    "acquisition": "ACQUISITION",
    "merger": "MERGER",
    "lawsuit": "LEGAL",
    "regulation": "REGULATION",
    "approval": "APPROVAL",
    "investigation": "INVESTIGATION",
    "layoff": "RESTRUCTURING",
    "factory": "CAPEX",
    "investment": "CAPEX",
}

TOPIC_KEYWORDS = {
    "ai": "AI",
    "chip": "SEMICONDUCTORS",
    "cloud": "CLOUD",
    "data": "DATA",
    "defense": "DEFENSE",
    "energy": "ENERGY",
    "automotive": "AUTOMOTIVE",
    "crypto": "CRYPTO",
    "bank": "FINANCE",
}


def extract_keywords(text: str):
    """
    Extract structured EVENT and TOPIC keywords from text.
    """
    t = text.lower()
    tags = []

    for k, v in EVENT_KEYWORDS.items():
        if k in t:
            tags.append(f"EVENT:{v}")

    for k, v in TOPIC_KEYWORDS.items():
        if re.search(rf"\b{k}\b", t):
            tags.append(f"TOPIC:{v}")

    return list(set(tags))


def fetch_news_for_guest(ticker: str, max_items: int = 8):
    api_key = st.secrets.get("NEWSDATA_API_KEY")
    if not api_key:
        return []

    company = COMPANY_MAP.get(ticker, ticker)

    # Strongly anchored query
    query = f'"{company}" OR {ticker}'

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
            "Ticker": ticker,
            "Company": company,
            "Title": a.get("title", ""),
            "Published": a.get("pubDate", ""),
            "Keywords": extract_keywords(text),
            "Raw_Text": text[:500],
        })

    return articles