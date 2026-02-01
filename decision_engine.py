"""
decision_engine.py
------------------
Final Decision Matrix
Fuses SLED, Rooms, Coupling, and News into a final action
"""

def final_decision(
    sled_signal: str,
    prepare: bool,
    coupling: dict,
    narrative_pressure: float,
    warp_ready: float | None = None,
):
    """
    Returns: (final_action, confidence, explanation)
    """

    confidence = 0.0
    reasons = []

    # ---------------- BASE ----------------
    if sled_signal == "BUY":
        confidence += 0.6
        reasons.append("SLED_BUY")
    elif sled_signal == "SELL":
        confidence += 0.6
        reasons.append("SLED_SELL")
    elif prepare:
        confidence += 0.3
        reasons.append("PREPARE")

    # ---------------- COUPLING ----------------
    if coupling:
        total = coupling.get("Total_Coupling", 0.0)
        confidence += total * 0.3
        if total >= 0.7:
            reasons.append("STRONG_COUPLING")
        elif total >= 0.4:
            reasons.append("MODERATE_COUPLING")

    # ---------------- NARRATIVE ----------------
    if narrative_pressure > 0:
        confidence += narrative_pressure * 0.2
        reasons.append("POSITIVE_NEWS")
    elif narrative_pressure < 0:
        confidence += abs(narrative_pressure) * 0.2
        reasons.append("NEGATIVE_NEWS")

    # ---------------- WARP ----------------
    if warp_ready is not None:
        confidence += warp_ready * 0.2
        if warp_ready > 0.8:
            reasons.append("WARP_READY")

    confidence = round(min(confidence, 1.0), 3)

    # ---------------- ACTION LOGIC ----------------
    if sled_signal == "BUY" and confidence >= 0.6:
        action = "BUY"
    elif sled_signal == "SELL" and confidence >= 0.6:
        action = "SELL"
    elif prepare and confidence >= 0.55:
        action = "BUY"
    elif confidence < 0.25:
        action = "WAIT"
    else:
        action = "PREPARE"

    return action, confidence, reasons