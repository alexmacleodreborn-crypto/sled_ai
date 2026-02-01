"""
coupling_engine.py
------------------
Detects reinforcement within and across rooms
"""

from collections import Counter
from itertools import combinations


def compute_internal_coupling(room: dict) -> float:
    """
    Measures reinforcement within a single room.
    """
    txs = room.get("Transactions", [])
    if not txs:
        return 0.0

    qualities = [t["Signal_Quality"] for t in txs]
    avg_quality = sum(qualities) / len(qualities)

    event_tags = []
    for t in txs:
        event_tags.extend(
            tag for tag in t.get("Tags", []) if tag.startswith("EVENT:")
        )

    event_diversity = len(set(event_tags)) / max(1, len(event_tags))
    repetition_bonus = 1.0 if len(event_tags) >= 2 else 0.0

    score = (
        avg_quality * 0.6 +
        (1 - event_diversity) * 0.2 +
        repetition_bonus * 0.2
    )

    return round(min(score, 1.0), 3)


def compute_external_coupling(rooms: dict, ticker: str) -> float:
    """
    Measures cross-room resonance.
    """
    if ticker not in rooms:
        return 0.0

    target_events = set()
    for t in rooms[ticker]["Transactions"]:
        for tag in t.get("Tags", []):
            if tag.startswith("EVENT:"):
                target_events.add(tag)

    if not target_events:
        return 0.0

    matches = 0
    comparisons = 0

    for other, room in rooms.items():
        if other == ticker:
            continue

        other_events = set()
        for t in room["Transactions"]:
            for tag in t.get("Tags", []):
                if tag.startswith("EVENT:"):
                    other_events.add(tag)

        if other_events:
            comparisons += 1
            if target_events & other_events:
                matches += 1

    if comparisons == 0:
        return 0.0

    return round(matches / comparisons, 3)


def coupling_state(score: float) -> str:
    if score >= 0.7:
        return "STRONG"
    if score >= 0.4:
        return "MODERATE"
    return "WEAK"


def update_couplings(state):
    """
    Updates coupling metrics for all rooms.
    """
    if "rooms" not in state:
        return

    rooms = state.rooms

    for ticker, room in rooms.items():
        internal = compute_internal_coupling(room)
        external = compute_external_coupling(rooms, ticker)

        total = round(internal * 0.6 + external * 0.4, 3)

        room["Coupling"] = {
            "Internal_Score": internal,
            "External_Score": external,
            "Total_Coupling": total,
            "Coupling_State": coupling_state(total),
        }