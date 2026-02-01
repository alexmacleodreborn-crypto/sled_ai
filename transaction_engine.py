"""
transaction_engine.py
---------------------
Doorman intake + noise reduction + tagging
"""

import re
import uuid
from datetime import datetime

EVENT_KEYWORDS = {
    "earnings": "EARNINGS",
    "guidance": "GUIDANCE",
    "acquisition": "ACQUISITION",
    "merger": "MERGER",
    "lawsuit": "LEGAL",
    "regulation": "REGULATION",
    "approval": "APPROVAL",
    "investigation": "INVESTIGATION",
}

SPECULATIVE_TERMS = {
    "may","might","could","possibly","rumor","speculation","believe"
}

OPINION_TERMS = {
    "think","feel","expect","likely","unlikely","seems"
}


def extract_ticker(text: str):
    m = re.findall(r"\b[A-Z]{2,5}\b", text)
    return m[0] if m else None


def score_signal_quality(text: str, ticker: str):
    score = 0.0
    t = text.lower()

    if ticker:
        score += 0.2

    if any(k in t for k in EVENT_KEYWORDS):
        score += 0.4

    if re.search(r"\d+(\.\d+)?%|\$\d+", text):
        score += 0.3

    if any(w in t for w in SPECULATIVE_TERMS):
        score -= 0.3

    if any(w in t for w in OPINION_TERMS):
        score -= 0.2

    return max(0.0, min(1.0, score))


def generate_tags(text: str, ticker: str):
    tags = []

    if ticker:
        tags.append(f"STOCK:{ticker}")

    for k, v in EVENT_KEYWORDS.items():
        if k in text.lower():
            tags.append(f"EVENT:{v}")

    return tags


def admit_transaction(source: str, raw_text: str):
    ticker = extract_ticker(raw_text)
    quality = score_signal_quality(raw_text, ticker)
    accepted = quality >= 0.4

    tx = {
        "Transaction_ID": f"TX-{uuid.uuid4().hex[:12].upper()}",
        "Timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "Source": source,
        "Ticker": ticker,
        "Raw_Text": raw_text[:500],
        "Signal_Quality": round(quality, 3),
        "Accepted": accepted,
        "Tags": generate_tags(raw_text, ticker) if accepted else [],
    }

    return tx