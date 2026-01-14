import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================================================
# Page configuration
# ==================================================
st.set_page_config(
    page_title="Mag’s Law & Sandy’s Square",
    layout="wide"
)

st.title("Mag’s Law → Sandy’s Square")
st.caption(
    "Structural progression under Sandy’s Law: "
    "right → right → right → revolution"
)

# ==================================================
# Sidebar navigation
# ==================================================
view = st.sidebar.radio(
    "View",
    [
        "Mag’s Law (Persistence / LRD)",
        "Sandy’s Square (Stepwise Trajectory)"
    ],
    key="view_selector"
)

# ==================================================
# Data upload
# ==================================================
st.sidebar.header("Data Input")

uploaded = st.sidebar.file_uploader(
    "Upload CSV (columns: time, mag)",
    type=["csv"],
    key="csv_uploader"
)

if uploaded is None:
    st.info(
        "⬅️ Upload a CSV to begin.\n\n"
        "Required columns:\n"
        "- time\n"
        "- mag"
    )
    st.stop()

# ==================================================
# Load and validate data
# ==================================================
df = pd.read_csv(uploaded)

required_cols = {"time", "mag"}
if not required_cols.issubset(df.columns):
    st.error(
        f"CSV must contain columns: {required_cols}\n"
        f"Found: {list(df.columns)}"
    )
    st.stop()

df = (
    df[["time", "mag"]]
    .dropna()
    .sort_values("time")
    .reset_index(drop=True)
)

if len(df) < 8:
    st.error("Need at least ~8 data points.")
    st.stop()

# ==================================================
# Σ — Observable Information
# ==================================================
m0 = float(df["mag"].iloc[0])
df["flux_proxy"] = 10 ** (-0.4 * (df["mag"] - m0))

df["delta_flux"] = df["flux_proxy"].diff().abs().fillna(0.0)
df["Sigma"] = df["delta_flux"].cumsum()

sigma_max = float(df["Sigma"].max())
df["Sigma_norm"] = df["Sigma"] / sigma_max if sigma_max > 0 else 0.0

# ==================================================
# Sidebar — Mag’s Law detection controls
# ==================================================
st.sidebar.header("Mag’s Law Detection")

slope_win = st.sidebar.slider(
    "Σ slope window (points)",
    3, min(12, len(df)), 5, 1,
    key="sigma_slope_window"
)

thr_q = st.sidebar.slider(
    "Persistence threshold quantile",
    0.05, 0.50, 0.20, 0.01,
    key="persistence_quantile"
)

min_persist_pts = st.sidebar.slider(
    "Min persistence length (points)",
    3, 12, 4, 1,
    key="min_persist_points"
)

# ==================================================
# Rolling slope helper
# ==================================================
def rolling_slope(t, y, window):
    out = np.full(len(y), np.nan)
    for i in range(window - 1, len(y)):
        tt = t[i - window + 1 : i + 1]
        yy = y[i - window + 1 : i + 1]
        if np.allclose(tt, tt[0]):
            out[i] = 0.0
        else:
            out[i] = np.polyfit(tt, yy, 1)[0]
    return out

t = df["time"].to_numpy(float)
df["dSigma_dt"] = rolling_slope(
    t, df["Sigma_norm"].to_numpy(float), slope_win
)

valid_slopes = df["dSigma_dt"].dropna().to_numpy()
slope_threshold = float(np.quantile(valid_slopes, thr_q))

df["PersistMask"] = df["dSigma_dt"].fillna(np.inf) <= slope_threshold

# Detect initial persistence block
persist_start = 0
persist_end = None
if df.loc[0, "PersistMask"]:
    end = 0
    for i in range(1, len(df)):
        if df.loc[i, "PersistMask"]:
            end = i
        else:
            break
    if (end - persist_start + 1) >= min_persist_pts:
        persist_end = end

df["PersistSegment"] = False
if persist_end is not None:
    df.loc[persist_start:persist_end, "PersistSegment"] = True

# Regime labels
df["Regime"] = "Transition"
df.loc[df["PersistSegment"], "Regime"] = "Persistence"
if persist_end is not None and persist_end + 1 < len(df):
    df.loc[persist_end + 1 :, "Regime"] = "Release"

# ==================================================
# Z — Structural Constraint (Option A)
# ==================================================
st.sidebar.header("Z (Structural Constraint)")

z_win = st.sidebar.slider(
    "Z variability window (points)",
    3, min(12, len(df)), 5, 1,
    key="z_variability_window"
)

df["flux_var"] = (
    df["flux_proxy"]
    .rolling(window=z_win, center=True)
    .var()
)

df["flux_var"] = df["flux_var"].bfill().ffill()

var_max = float(df["flux_var"].max())
df["Z"] = 1.0 - (df["flux_var"] / var_max) if var_max > 0 else 1.0

# ==================================================
# VIEW 1 — MAG’S LAW
# ==================================================
if view == "Mag’s Law (Persistence / LRD)":

    st.header("Mag’s Law — Persistence (Low-Radiance Domain)")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["time"], df["mag"], marker="o", color="black")

    if persist_end is not None:
        ax.axvspan(
            df.loc[persist_start, "time"],
            df.loc[persist_end, "time"],
            color="tab:blue",
            alpha=0.15,
            label="Mag’s Law"
        )

    ax.invert_yaxis()
    ax.set_xlabel("Time")
    ax.set_ylabel("Magnitude")
    ax.set_title("Light Curve with Mag’s Law Interval")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    st.pyplot(fig)

    fig2, ax2 = plt.subplots(figsize=(9, 4))
    ax2.plot(df["time"], df["Sigma_norm"], marker="o", color="tab:blue")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Σ (normalised)")
    ax2.set_title("Observable Information Accumulation (Σ)")
    ax2.grid(True, alpha=0.3)

    st.pyplot(fig2)

# ==================================================
# VIEW 2 — SANDY’S SQUARE (STEPWISE)
# ==================================================
else:

    st.header("Sandy’s Square — Stepwise Structural Trajectory")

    st.markdown(
        """
**Rightward motion** = internal structural progression (Z evolves, Σ flat)  
**Revolution** = forced dimensional change (Σ jumps)

This is **not smooth evolution**.
"""
    )

    fig, ax = plt.subplots(figsize=(6.8, 6.8))

    colors = {
        "Persistence": "tab:blue",
        "Transition": "tab:orange",
        "Release": "tab:red"
    }

    # Scatter points
    for regime, g in df.groupby("Regime"):
        ax.scatter(
            g["Z"], g["Sigma_norm"],
            label=regime,
            s=55,
            alpha=0.8,
            color=colors.get(regime, "gray"),
            zorder=3
        )

    # Stepwise trajectory
    Z = df["Z"].to_numpy()
    S = df["Sigma_norm"].to_numpy()

    for i in range(len(df) - 1):
        dz = Z[i + 1] - Z[i]
        ds = S[i + 1] - S[i]

        if abs(ds) > 0.08:
            # Revolution (vertical jump)
            ax.plot(
                [Z[i], Z[i + 1]],
                [S[i], S[i + 1]],
                color="black",
                linewidth=2.3,
                alpha=0.95,
                zorder=4
            )
        else:
            # Rightward structural step
            ax.plot(
                [Z[i], Z[i + 1]],
                [S[i], S[i + 1]],
                color="black",
                linewidth=0.8,
                alpha=0.35,
                zorder=2
            )

    ax.set_xlabel("Z — Structural Constraint (Rightward)")
    ax.set_ylabel("Σ — Observable Information (Revolution)")
    ax.set_title("Sandy’s Square: right → right → right → revolution")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    st.pyplot(fig)

# ==================================================
# Export
# ==================================================
st.sidebar.header("Export")

csv_bytes = df.to_csv(index=False).encode("utf-8")

st.sidebar.download_button(
    "Download results CSV",
    data=csv_bytes,
    file_name="sandys_square_export.csv",
    mime="text/csv",
    key="download_results"
)

# ==================================================
# Footer
# ==================================================
st.divider()
st.caption(
    "Mag’s Law & Sandy’s Square | Sandy’s Law Framework | "
    "Deterministic • Structural • Reproducible"
)
