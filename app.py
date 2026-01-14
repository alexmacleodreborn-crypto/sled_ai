import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Mag’s Law — Persistence (LRD)",
    layout="wide"
)

st.title("Mag’s Law — Persistence (Low-Radiance Domain)")
st.caption(
    "A structural principle within Sandy’s Law: "
    "energy may exist and evolve internally while remaining observationally silent"
)

# --------------------------------------------------
# Sidebar navigation
# --------------------------------------------------
view = st.sidebar.radio(
    "View",
    [
        "Mag’s Law (Persistence / LRD)",
        "Structural State Space (Sandy’s Square)"
    ]
)

# --------------------------------------------------
# Data upload
# --------------------------------------------------
st.sidebar.header("Data Input")

uploaded = st.sidebar.file_uploader(
    "Upload Supernova B-band CSV (time, mag)",
    type=["csv"]
)

if uploaded is None:
    st.info(
        "⬅️ Upload a B-band supernova CSV to begin.\n\n"
        "Required columns:\n"
        "- `time`\n"
        "- `mag`"
    )
    st.stop()

# --------------------------------------------------
# Load and validate CSV
# --------------------------------------------------
try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

required_cols = {"time", "mag"}
if not required_cols.issubset(df.columns):
    st.error(
        "CSV must contain columns: `time` and `mag`.\n\n"
        f"Found columns: {list(df.columns)}"
    )
    st.stop()

df = (
    df[["time", "mag"]]
    .dropna()
    .sort_values("time")
    .reset_index(drop=True)
)

if len(df) < 6:
    st.error("Need at least ~6 points to estimate Σ slope robustly.")
    st.stop()

# --------------------------------------------------
# Observable Information Σ (event-scaled)
# --------------------------------------------------
# Convert magnitude to relative flux proxy
m0 = float(df["mag"].iloc[0])
df["flux_proxy"] = 10 ** (-0.4 * (df["mag"] - m0))

# Incremental observable change
df["delta_flux"] = df["flux_proxy"].diff().abs().fillna(0.0)

# Cumulative observable information
df["Sigma"] = df["delta_flux"].cumsum()

# Normalised Sigma for plotting
sigma_max = float(df["Sigma"].max())
df["Sigma_norm"] = df["Sigma"] / sigma_max if sigma_max > 0 else 0.0

# --------------------------------------------------
# Step B: Automatic Mag’s Law interval detection
# --------------------------------------------------
# We detect persistence by a low slope of Σ over time.
# Use a rolling linear slope estimate for robustness.

with st.sidebar:
    st.header("Mag’s Law Detection (Step B)")
    slope_win = st.slider("Slope window (points)", 3, min(12, len(df)), 5, 1)
    # Threshold set as a quantile of slopes so it adapts across datasets
    thr_q = st.slider("Persistence threshold quantile", 0.05, 0.50, 0.20, 0.01)
    min_persist_pts = st.slider("Min persistence length (points)", 3, 12, 4, 1)

def rolling_slope(t: np.ndarray, y: np.ndarray, window: int) -> np.ndarray:
    """
    Rolling linear slope dy/dt using least squares over a moving window.
    Returns an array same length as y (NaN for early points without full window).
    """
    n = len(y)
    out = np.full(n, np.nan, dtype=np.float64)
    for i in range(window - 1, n):
        tt = t[i - window + 1 : i + 1]
        yy = y[i - window + 1 : i + 1]
        # Guard against identical times (shouldn't happen, but safe)
        if np.allclose(tt, tt[0]):
            out[i] = 0.0
            continue
        # Fit slope
        m, _b = np.polyfit(tt, yy, 1)
        out[i] = m
    return out

t = df["time"].to_numpy(dtype=np.float64)
sigma = df["Sigma_norm"].to_numpy(dtype=np.float64)

df["dSigma_dt"] = rolling_slope(t, sigma, slope_win)

# Determine threshold from data distribution (adaptive)
valid_slopes = df["dSigma_dt"].dropna().to_numpy()
if len(valid_slopes) == 0:
    st.error("Could not compute Σ slopes (insufficient valid data).")
    st.stop()

# Persistence threshold: low-slope region
slope_threshold = float(np.quantile(valid_slopes, thr_q))

# Persistence mask where slope is below threshold
df["PersistMask"] = df["dSigma_dt"].fillna(np.inf) <= slope_threshold

# Find earliest contiguous persistence segment from the start
# (Mag’s Law is the initial persistence regime)
persist_indices = np.where(df["PersistMask"].to_numpy())[0]

persist_start = 0
persist_end = None

if len(persist_indices) > 0 and persist_indices[0] == 0:
    # walk until break
    end = 0
    for i in range(1, len(df)):
        if df.loc[i, "PersistMask"]:
            end = i
        else:
            break
    # enforce minimum length
    if (end - persist_start + 1) >= min_persist_pts:
        persist_end = end

# If not found, fall back to "no detected persistence"
df["PersistSegment"] = False
if persist_end is not None:
    df.loc[persist_start : persist_end, "PersistSegment"] = True

# Define "Mag’s Law exit" time (first index after persistence)
exit_idx = None
if persist_end is not None and persist_end + 1 < len(df):
    exit_idx = persist_end + 1

# --------------------------------------------------
# VIEW 1 — MAG’S LAW / PERSISTENCE
# --------------------------------------------------
if view == "Mag’s Law (Persistence / LRD)":

    st.header("Mag’s Law — Persistence (Low-Radiance Domain)")

    st.markdown(
        """
**Mag’s Law (Persistence Law)** describes a regime in which energy exists
and evolves internally, yet observable radiation remains suppressed due
to strong structural constraints.

In this regime:
- Energy ≠ observability
- Photons exist but remain mass-coupled and trapped
- Observable information does not accumulate

This regime is referred to as the **Low-Radiance Domain (LRD)**.
"""
    )

    # --------------------------------------------------
    # Light curve (with persistence highlight)
    # --------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.plot(df["time"], df["mag"], marker="o", linestyle="-", color="black")

    # Shade detected Mag’s Law persistence interval
    if persist_end is not None:
        t0 = float(df.loc[persist_start, "time"])
        t1 = float(df.loc[persist_end, "time"])
        ax.axvspan(t0, t1, alpha=0.15, color="tab:blue", label="Mag’s Law (detected)")

        # Mark exit
        if exit_idx is not None:
            tx = float(df.loc[exit_idx, "time"])
            ax.axvline(tx, linestyle="--", alpha=0.5, color="tab:red", label="Exit")

    ax.invert_yaxis()
    ax.set_xlabel("Time")
    ax.set_ylabel("B-band Magnitude")
    ax.set_title("Supernova B-band Light Curve (Mag’s Law Interval Highlighted)")
    ax.grid(True, alpha=0.3)

    if persist_end is not None:
        ax.legend(frameon=False, loc="best")

    st.pyplot(fig)

    if persist_end is None:
        st.warning(
            "Mag’s Law interval was not automatically detected with current settings. "
            "Try increasing the slope window or raising the threshold quantile."
        )
    else:
        st.success(
            f"Detected Mag’s Law interval: index 0 → {persist_end} "
            f"(time {df.loc[persist_start,'time']:.4f} → {df.loc[persist_end,'time']:.4f})"
        )

    # --------------------------------------------------
    # Observable Information Σ (with persistence highlight)
    # --------------------------------------------------
    st.subheader("Observable Information Accumulation (Σ) — with Mag’s Law Detection")

    st.markdown(
        """
Σ (Sigma) is a **proxy for observable information**, defined here as the
cumulative magnitude of observed change in the signal.

**Step B:** We identify the Mag’s Law interval automatically by detecting
a **near-zero slope** of Σ early in the sequence, then marking the first
significant rise as the exit from persistence.
"""
    )

    fig2, ax2 = plt.subplots(figsize=(9, 4))
    ax2.plot(df["time"], df["Sigma_norm"], marker="o", linestyle="-", color="tab:blue", label="Σ (norm)")

    # Shade persistence interval
    if persist_end is not None:
        t0 = float(df.loc[persist_start, "time"])
        t1 = float(df.loc[persist_end, "time"])
        ax2.axvspan(t0, t1, alpha=0.15, color="tab:blue", label="Mag’s Law (detected)")

        if exit_idx is not None:
            tx = float(df.loc[exit_idx, "time"])
            ax2.axvline(tx, linestyle="--", alpha=0.5, color="tab:red", label="Exit")

    ax2.set_xlabel("Time")
    ax2.set_ylabel("Normalised Σ")
    ax2.set_title("Cumulative Observable Information (Σ)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(frameon=False, loc="best")

    st.pyplot(fig2)

    # Show slope diagnostics
    with st.expander("Σ slope diagnostics", expanded=False):
        st.write(f"Slope window: {slope_win} points")
        st.write(f"Persistence threshold quantile: {thr_q:.2f}")
        st.write(f"Slope threshold (dΣ/dt): {slope_threshold:.6g}")
        st.dataframe(df[["time", "mag", "Sigma_norm", "dSigma_dt", "PersistMask", "PersistSegment"]])

    st.markdown(
        """
**Key point (Mag’s Law):**  
A system does not become visible when energy is created.  
It becomes visible when **observable information begins to accumulate** and persistence ends.
"""
    )

# --------------------------------------------------
# VIEW 2 — SANDY’S SQUARE (NEXT STEP)
# --------------------------------------------------
else:

    st.header("Structural State Space (Sandy’s Square)")

    st.warning(
        "Sandy’s Square is still disabled.\n\n"
        "Now that Mag’s Law can be detected automatically (Step B), the next step is:\n"
        "- define structural constraint (Z)\n"
        "- map the trajectory in (Z, Σ)\n"
        "- show boundary crossing from Mag’s Law → transition → release"
    )

    st.markdown(
        """
The Square becomes meaningful only after Mag’s Law is **detected**, not hand-labeled.
You’ve now achieved that.
"""
    )

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption(
    "Mag’s Law — Persistence Demonstration | "
    "Part of Sandy’s Law | CSV-based • Deterministic • Reproducible"
)
