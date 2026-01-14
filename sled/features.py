import numpy as np
import pandas as pd

def rolling_entropy_from_returns(x: pd.Series, win: int, bins: int = 16) -> pd.Series:
    r = x.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    def ent(window):
        hist, _ = np.histogram(window, bins=bins, density=True)
        p = hist / (hist.sum() + 1e-12)
        p = p[p > 0]
        return float(-(p * np.log2(p)).sum())

    return r.rolling(win, min_periods=win).apply(ent, raw=False)

def structural_constraint_proxy(x: pd.Series, win: int) -> pd.Series:
    r = x.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    vol = r.rolling(win, min_periods=win).std(ddof=0)

    vmin = vol.rolling(win, min_periods=win).min()
    vmax = vol.rolling(win, min_periods=win).max()
    openness = ((vol - vmin) / (vmax - vmin + 1e-12)).clip(0, 1)

    Z = (1 - openness).clip(0, 1)
    return Z

def compute_sled_features(df: pd.DataFrame, win: int = 64) -> pd.DataFrame:
    out = df.copy()
    out["Sigma"] = rolling_entropy_from_returns(out["x"], win)
    out["Z"] = structural_constraint_proxy(out["x"], win)
    out["G"] = (1 - out["Z"]) * out["Sigma"]
    return out
