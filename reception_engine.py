"""
reception_engine.py
-------------------
Reception + Room state management
"""

from datetime import datetime
from collections import defaultdict


def init_rooms(state):
    if "rooms" not in state:
        state.rooms = {}


def check_in_transaction(state, tx: dict):
    """
    Assign an accepted transaction to a room.
    """
    if not tx.get("Accepted"):
        return

    ticker = tx.get("Ticker")
    if not ticker:
        return

    if ticker not in state.rooms:
        state.rooms[ticker] = {
            "Ticker": ticker,
            "Created": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "Last_Updated": None,
            "Transactions": [],
            "Event_Counts": defaultdict(int),
            "Avg_Signal_Quality": 0.0,
            "Last_Event": None,
        }

    room = state.rooms[ticker]
    room["Transactions"].append(tx)
    room["Last_Updated"] = tx["Timestamp"]

    # Update event counts
    for tag in tx.get("Tags", []):
        if tag.startswith("EVENT:"):
            event = tag.split("EVENT:")[1]
            room["Event_Counts"][event] += 1
            room["Last_Event"] = event

    # Update average signal quality
    qualities = [t["Signal_Quality"] for t in room["Transactions"]]
    room["Avg_Signal_Quality"] = round(sum(qualities) / len(qualities), 3)