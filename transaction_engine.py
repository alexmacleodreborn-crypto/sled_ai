"""
transaction_engine.py
---------------------
Doorman intake + noise reduction + tagging
"""

import re
import uuid
from datetime import datetime


# ==================================================
# KEYWORD SETS
# ==================================================
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
    "may", "might", "could", "possibly", "rumor", "speculation", "believe"
}

OPINION_TERMS = {
    "think", "feel", "expect", "likely", "unlikely", "seems"
}


# ==================================================
# EXTRACTION & SCORING
# ==================================================
def extract_ticker(text: str):
    """
    Extract first uppercase ticker-like token.
    """
    matches = re.findall(r"\b[A-Z]{2,5}\b", text)
    return matches[0] if matches else None


def score_signal_quality(text: str, ticker: str | None):
    """
    Quantifies informational value of input.
    """
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


def generate_tags(text: str, ticker: str | None):
    """
    Generates minimal, high-signal tags.
    """
    tags = []

    if ticker:
        tags.append(f"STOCK:{ticker}")

    for key, tag in EVENT_KEYWORDS.items():
        if key in text.lower():
            tags.append(f"EVENT:{tag}")

    return tags


# ==================================================
# DOORMAN ENTRY (MANUAL OR FILE)
# ==================================================
def admit_transaction(source: str, raw_text: str):
    """
    Core Doorman admission logic.
    """
    ticker = extract_ticker(raw_text)
    quality = score_signal_quality(raw_text, ticker)
    accepted = quality >= 0.4

    return {
        "Transaction_ID": f"TX-{uuid.uuid4().hex[:12].upper()}",
        "Timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "Source": source,
        "Ticker": ticker,
        "Raw_Text": raw_text[:500],
        "Signal_Quality": round(quality, 3),
        "Accepted": accepted,
        "Tags": generate_tags(raw_text, ticker) if accepted else [],
    }


# ==================================================
# DOORMAN ENTRY (AUTOMATED SALES SCAN)
# ==================================================
def admit_scan_transaction(
    ticker: str,
    sled_summary: dict,
    news_profile: dict
):
    """
    Converts an automated scan result into a Doorman transaction.
    """

    text = (
        f"{ticker} scan | "
        f"SLED={sled_summary.get('Signal')} | "
        f"Gate={sled_summary.get('Gate')} | "
        f"Z={sled_summary.get('Z_Trap')} | "
        f"Sigma={sled_summary.get('Sigma')} | "
        f"News={news_profile.get('Sentiment')} | "
        f"Pressure={news_profile.get('Narrative_Pressure')}"
    )

    return admit_transaction(
        source="SALES_SCAN",
        raw_text=text
    )