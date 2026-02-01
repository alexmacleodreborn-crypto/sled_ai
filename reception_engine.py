"""
reception_engine.py
-------------------
Reception continuity & room state tracking
"""

from datetime import datetime
from collections import defaultdict


def init_rooms(state):
    if "rooms" not in state:
        state.rooms = {}


def _direction(curr, prev, tol=1e-6):
    if prev is None:
        return "INIT"
    if curr > prev + tol:
        return "RISING"
    if curr < prev - tol:
        return "FALLING"
    return "FLAT"


def check_in_transaction(state, tx: dict):
    """
    Check a transaction into the correct room
    and update temporal continuity.
    """
    if not tx.get("Accepted"):
        return

    ticker = tx.get("Ticker")
    if not ticker:
        return

    if ticker not in state.rooms:
        state.rooms[ticker] = {
            "Ticker": ticker,
            "First_CheckIn": tx["Timestamp"],
            "Last_CheckIn": None,
            "History": [],
            "Transitions": {},
            "Transactions": [],
            "Event_Counts": defaultdict(int),
            "Avg_Signal_Quality": 0.0,
        }

    room = state.rooms[ticker]

    # ------------------------------------------------
    # Transaction memory
    # ------------------------------------------------
    room["Transactions"].append(tx)
    room["Last_CheckIn"] = tx["Timestamp"]

    for tag in tx.get("Tags", []):
        if tag.startswith("EVENT:"):
            room["Event_Counts"][tag.split(":")[1]] += 1

    qualities = [t["Signal_Quality"] for t in room["Transactions"]]
    room["Avg_Signal_Quality"] = round(sum(qualities) / len(qualities), 3)

    # ------------------------------------------------
    # Temporal continuity (from AUTO_SCAN rows)
    # ------------------------------------------------
    if tx["Source"] == "AUTO_SCAN":

        # Parse structured scan text
        raw = tx["Raw_Text"]

        def extract_float(label):
            try:
                return float(
                    raw.split(f"{label}=")[1].split("|")[0]
                )
            except Exception:
                return None

        snapshot = {
            "Timestamp": tx["Timestamp"],
            "Price": extract_float("Price"),
            "Gate": extract_float("Gate"),
            "Z_Trap": extract_float("Z"),
            "Sigma": extract_float("Sigma"),
            "SLED_Signal": (
                raw.split("SLED=")[1].split("|")[0]
                if "SLED=" in raw else None
            )
        }

        history = room["History"]
        prev = history[-1] if history else {}

        room["Transitions"] = {
            "Price": _direction(snapshot["Price"], prev.get("Price")),
            "Gate": _direction(snapshot["Gate"], prev.get("Gate")),
            "Z_Trap": _direction(snapshot["Z_Trap"], prev.get("Z_Trap")),
            "Sigma": _direction(snapshot["Sigma"], prev.get("Sigma")),
        }

        history.append(snapshot)