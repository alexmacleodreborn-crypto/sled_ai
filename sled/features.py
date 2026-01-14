import numpy as np
import pandas as pd

# ==================================================
# Σ — Internal Information Density
# ==================================================
def rolling_entropy_from_returns(
    x: pd.Series,
    win: int,
    bins: int = 16
) -> pd.Series:
    """
    Shannon entropy of rolling return distributions.
    Measures internal information density (Σ).
    """

    r = x.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    def entropy(window):
        hist, _ = np.histogram(window, bins=bins, density=False)
        total = hist.sum()
        if total == 0:
            return np.nan
        p = hist / total
        p = p[p > 0]
        return float(-(p * np.log2(p)).sum())

    return r.rolling(win, min_periods=win).apply(entropy, raw=False)


# ==================================================
# Z — Structural Constraint (Compression-Aware)
# ==================================================
def structural_constraint_proxy(
    x: pd.Series,
    win: int
) -> pd.Series:
    """
    Structural constraint Z measures suppression of observable motion
    relative to internal pressure.

    High Z:
      - internal activity present
      - observable movement suppressed

    Low Z:
      - structure has opened
      - motion released
    """

    # Observable motion
    r = x.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    vol = r.rolling(win, min_periods=win).std(ddof=0)

    # Internal pressure proxy (persistent micro-movement)
    pressure = r.abs().rolling(win, min_periods=win).mean()

    # Constraint = pressure exists but motion suppressed
    Z_raw = pressure / (vol + 1e-6)

    # Normalize into [0,1]
    Z_min = Z_raw.rolling(win, min_periods=win).min()
    Z_max = Z_raw.rolling(win, min_periods=win).max()

    Z = (Z_raw - Z_min) / (Z_max - Z_min + 1e-6)

    return Z.clip(0.0, 1.0)


# ==================================================
# G — Entropic Gate
# ==================================================
def compute_sled_features(
    df: pd.DataFrame,
    win: int = 64
) -> pd.DataFrame:
    """
    Compute full SLED feature set:
      - Σ (entropy / internal pressure)
      - Z (structural constraint)
      - G (gate openness)
    """

    out = df.copy()

    out["Sigma"] = rolling_entropy_from_returns(out["x"], win=win)
    out["Z"] = structural_constraint_proxy(out["x"], win=win)

    # Gate opens when constraint falls
    out["G"] = (1.0 - out["Z"]) * out["Sigma"]

    return out
