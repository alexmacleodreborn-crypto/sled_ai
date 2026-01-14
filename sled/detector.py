import numpy as np
import pandas as pd

def phase0_flags(
    df: pd.DataFrame,
    slope_win: int = 12,
    z_high: float = 0.75,
    z_stable_max_std: float = 0.05,
    sigma_slope_min: float = 0.0,
) -> pd.DataFrame:
    out = df.copy()

    def slope(arr):
        if np.any(np.isnan(arr)):
            return np.nan
        x = np.arange(len(arr))
        return float(np.polyfit(x, arr, 1)[0])

    out["Sigma_slope"] = out["Sigma"].rolling(slope_win, min_periods=slope_win).apply(slope, raw=True)
    out["Z_std"] = out["Z"].rolling(slope_win, min_periods=slope_win).std(ddof=0)

    out["Phase0"] = (
        (out["Sigma_slope"] > sigma_slope_min) &
        (out["Z"] >= z_high) &
        (out["Z_std"] <= z_stable_max_std)
    )
    return out
