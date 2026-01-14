import numpy as np
import pandas as pd

# ==================================================
# Helpers
# ==================================================
def _slope(series_window: np.ndarray) -> float:
    """
    Simple linear slope via polyfit on a window.
    Returns NaN if window contains NaNs.
    """
    if np.any(np.isnan(series_window)):
        return np.nan
    x = np.arange(len(series_window))
    return float(np.polyfit(x, series_window, 1)[0])

def _minmax_01(s: pd.Series, eps: float = 1e-12) -> pd.Series:
    mn = s.min(skipna=True)
    mx = s.max(skipna=True)
    if pd.isna(mn) or pd.isna(mx) or abs(mx - mn) < eps:
        return s * np.nan
    return ((s - mn) / (mx - mn + eps)).clip(0.0, 1.0)

def _sigmoid(x: pd.Series, k: float = 10.0) -> pd.Series:
    return 1.0 / (1.0 + np.exp(-k * x))

# ==================================================
# Full SLED detection: Phase0 + Release + Regime
# ==================================================
def sled_detect(
    df: pd.DataFrame,
    slope_win: int = 12,

    # Phase-0 thresholds
    z_high: float = 0.70,
    z_stable_max_std: float = 0.08,
    sigma_slope_min: float = 0.00,

    # Release thresholds
    z_drop_min: float = 0.10,      # how much Z must drop (window-to-window)
    g_rise_min: float = 0.10,      # how much G must rise
    r_spike_q: float = 0.95,       # return spike quantile for release

    # Regime thresholds
    z_trapped: float = 0.75,
    z_open: float = 0.35,
) -> pd.DataFrame:
    """
    Adds:
      - Sigma_slope
      - Z_std
      - dZ (negative = constraint dropping)
      - dG (positive = gate output rising)
      - Phase0_score, Phase0
      - Release_score, Release
      - Regime (Trapped/Transitional/Escaping)
    """
    out = df.copy()

    # Slopes / stability
    out["Sigma_slope"] = out["Sigma"].rolling(slope_win, min_periods=slope_win).apply(_slope, raw=True)
    out["Z_std"] = out["Z"].rolling(slope_win, min_periods=slope_win).std(ddof=0)

    # First differences
    out["dZ"] = out["Z"].diff()
    out["dG"] = out["G"].diff()

    # ------------------------------
    # Phase-0 scoring (continuous)
    #   want:
    #     Sigma_slope high
    #     Z high
    #     Z_std low (stable constraint)
    # ------------------------------
    sigma_term = _sigmoid(_minmax_01(out["Sigma_slope"].fillna(0.0)) - 0.3, k=8.0)
    z_term = _sigmoid(out["Z"].fillna(0.0) - z_high, k=12.0)
    stable_term = _sigmoid((z_stable_max_std - out["Z_std"].fillna(z_stable_max_std)) / max(z_stable_max_std, 1e-6), k=12.0)

    out["Phase0_score"] = (sigma_term * z_term * stable_term).clip(0.0, 1.0)

    out["Phase0"] = (
        (out["Sigma_slope"] > sigma_slope_min) &
        (out["Z"] >= z_high) &
        (out["Z_std"] <= z_stable_max_std)
    )

    # ------------------------------
    # Release scoring
    #   want:
    #     Z drops fast (dZ negative, magnitude large)
    #     G rises fast (dG positive)
    #     return spike (|r| high)
    # ------------------------------
    dz_drop = (-out["dZ"]).clip(lower=0.0)  # positive when Z is dropping
    dg_rise = (out["dG"]).clip(lower=0.0)

    dz_term = _sigmoid(dz_drop.fillna(0.0) - z_drop_min, k=12.0)
    dg_term = _sigmoid(dg_rise.fillna(0.0) - g_rise_min, k=12.0)

    absr = out.get("r", pd.Series(index=out.index, dtype=float)).abs()
    spike_thr = absr.quantile(r_spike_q) if absr.notna().any() else np.nan
    spike_term = _sigmoid(absr.fillna(0.0) - (spike_thr if pd.notna(spike_thr) else 0.0), k=12.0)

    out["Release_score"] = (dz_term * dg_term * spike_term).clip(0.0, 1.0)

    out["Release"] = (
        (dz_drop > z_drop_min) &
        (dg_rise > g_rise_min) &
        (absr >= spike_thr if pd.notna(spike_thr) else False)
    )

    # ------------------------------
    # Regime label
    # ------------------------------
    regime = []
    for z in out["Z"].fillna(np.nan).to_list():
        if np.isnan(z):
            regime.append(None)
        elif z >= z_trapped:
            regime.append("Trapped")
        elif z <= z_open:
            regime.append("Escaping")
        else:
            regime.append("Transitional")

    out["Regime"] = regime

    return out
