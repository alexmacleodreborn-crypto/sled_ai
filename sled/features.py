import numpy as np
import pandas as pd

# ==================================================
# Helpers
# ==================================================
def _safe_series(s: pd.Series) -> pd.Series:
    return s.replace([np.inf, -np.inf], np.nan)

def _rolling_shannon_entropy(values: np.ndarray, bins: int) -> float:
    """
    Shannon entropy of values binned into `bins` equally spaced bins.
    Returns NaN if not enough non-NaN values.
    """
    v = values[~np.isnan(values)]
    if v.size < 3:
        return np.nan
    hist, _ = np.histogram(v, bins=bins, density=False)
    total = hist.sum()
    if total <= 0:
        return np.nan
    p = hist / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())

def rolling_entropy(x: pd.Series, win: int, bins: int = 16) -> pd.Series:
    """
    Σ(t): internal information density.
    Implemented as rolling Shannon entropy of returns distribution.
    """
    r = _safe_series(x.pct_change()).fillna(0.0)

    def ent(window):
        return _rolling_shannon_entropy(np.asarray(window), bins=bins)

    return r.rolling(win, min_periods=win).apply(ent, raw=False)

def rolling_volatility(x: pd.Series, win: int) -> pd.Series:
    """
    O(t): external motion / observability proxy.
    Implemented as rolling std of returns.
    """
    r = _safe_series(x.pct_change()).fillna(0.0)
    return r.rolling(win, min_periods=win).std(ddof=0)

def rolling_quantile_scale(s: pd.Series, win: int, q_low: float = 0.10, q_high: float = 0.90) -> pd.Series:
    """
    Robust normalization into [0,1] using rolling quantiles.
    Prevents collapse when s is flat / compressed.
    """
    lo = s.rolling(win, min_periods=win).quantile(q_low)
    hi = s.rolling(win, min_periods=win).quantile(q_high)

    denom = (hi - lo).replace(0, np.nan)
    scaled = (s - lo) / (denom + 1e-12)
    return scaled.clip(0.0, 1.0)

def structural_constraint_Z(observability_O: pd.Series, win: int) -> pd.Series:
    """
    Z(t): structural constraint in [0,1].
    High Z => trapped (low observability), Low Z => open (high observability)

    Z = 1 - Norm(O)
    where Norm is robust rolling quantile scaling.
    """
    O_norm = rolling_quantile_scale(observability_O, win=win, q_low=0.10, q_high=0.90)
    Z = (1.0 - O_norm).clip(0.0, 1.0)
    return Z

def entropic_gate_G(Sigma: pd.Series, Z: pd.Series) -> pd.Series:
    """
    G(t) = (1 - Z(t)) * Sigma(t)
    """
    return (1.0 - Z) * Sigma

# ==================================================
# Public API
# ==================================================
def compute_sled_features(
    df: pd.DataFrame,
    win: int = 64,
    entropy_bins: int = 16
) -> pd.DataFrame:
    """
    Computes the full SLED feature stack.

    Inputs:
      df with columns: ["t","x"]
    Outputs (added columns):
      - r: returns
      - Sigma: entropy-based internal density
      - O: observability proxy (volatility)
      - Z: structural constraint (robust)
      - G: entropic gate output
    """
    out = df.copy()

    # Returns (used by downstream detectors)
    out["r"] = _safe_series(out["x"].pct_change()).fillna(0.0)

    # Core SLED variables
    out["Sigma"] = rolling_entropy(out["x"], win=win, bins=entropy_bins)
    out["O"] = rolling_volatility(out["x"], win=win)
    out["Z"] = structural_constraint_Z(out["O"], win=win)
    out["G"] = entropic_gate_G(out["Sigma"], out["Z"])

    return out
