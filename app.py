import streamlit as st
import pandas as pd
import numpy as np
import lightkurve as lk
import matplotlib.pyplot as plt

from sled.features import compute_sled_features
from sled.detector import sled_detect

# ==================================================
# Page config
# ==================================================
st.set_page_config(
    page_title="Sandy’s Square — TESS Photon Pipeline",
    layout="wide"
)

st.title("Sandy’s Square — TESS Photon Observability")
st.caption(
    "Real TESS photon data → Σ–Z Square → Phase-0 → Escape"
)

# ==================================================
# Sidebar controls
# ==================================================
with st.sidebar:
    st.header("TESS Target")

    target = st.text_input(
        "TIC ID or target name",
        value="TIC 307210830",
        help="Example: TIC 307210830"
    )

    cadence = st.selectbox(
        "Cadence",
        options=["short", "long"],
        index=0
    )

    st.divider()
    st.header("Sandy’s Square Parameters")

    win = st.slider("Feature window", 16, 256, 64, 8)
    entropy_bins = st.slider("Entropy bins (Σ)", 8, 64, 16, 4)
    slope_win = st.slider("Slope window", 6, 64, 12)

    z_high = st.slider("Z high (Phase-0)", 0.5, 0.95, 0.70, 0.01)
    z_stable = st.slider("Z stability (std)", 0.01, 0.25, 0.08, 0.01)
    sigma_slope_min = st.slider("Min Σ slope", -0.1, 0.2, 0.0, 0.01)

    z_drop_min = st.slider("Min ΔZ (release)", 0.01, 0.5, 0.10, 0.01)
    g_rise_min = st.slider("Min ΔG (release)", 0.01, 1.0, 0.10, 0.01)
    r_spike_q = st.slider("Return spike quantile", 0.5, 0.99, 0.95, 0.01)

    run = st.button("Fetch TESS & Run Sandy’s Square")

# ==================================================
# Guard
# ==================================================
if not run:
    st.info("⬅️ Enter a TESS target and click **Fetch TESS & Run**")
    st.stop()

# ==================================================
# Fetch TESS light curve
# ==================================================
with st.spinner("Fetching TESS photon data…"):
    try:
        search = lk.search_lightcurve(
            target,
            mission="TESS",
            cadence=cadence
        )
        if len(search) == 0:
            st.error("No TESS light curve found for this target.")
            st.stop()

        lc = search.download().PDCSAP_FLUX

    except Exception as e:
        st.error(f"TESS fetch failed: {e}")
        st.stop()

# ==================================================
# SAFE conversion: Astropy → NumPy → DataFrame
# ==================================================
try:
    t = np.asarray(lc.time.value, dtype=np.float64)
    x = np.asarray(lc.flux.value, dtype=np.float64)
except Exception as e:
    st.error(f"Data conversion failed: {e}")
    st.stop()

mask = np.isfinite(t) & np.isfinite(x)
df = pd.DataFrame({
    "t": t[mask],
    "x": x[mask]
}).reset_index(drop=True)

if df.empty:
    st.error("All data points invalid after cleaning.")
    st.stop()

if len(df) < win + slope_win + 5:
    st.warning(
        f"Only {len(df)} data points available. "
        f"Reduce window sizes for stable results."
    )

# ==================================================
# Run Sandy’s Square / SLED
# ==================================================
features = compute_sled_features(
    df,
    win=win,
    entropy_bins=entropy_bins
)

results = sled_detect(
    features,
    slope_win=slope_win,
    z_high=z_high,
    z_stable_max_std=z_stable,
    sigma_slope_min=sigma_slope_min,
    z_drop_min=z_drop_min,
    g_rise_min=g_rise_min,
    r_spike_q=r_spike_q,
)

# ==================================================
# Summary
# ==================================================
st.subheader("Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Data points", len(results))
c2.metric("Phase-0 count", int(results["Phase0"].sum()))
c3.metric("Release count", int(results["Release"].sum()))
c4.metric("Final regime", results["Regime"].iloc[-1])

# ==================================================
# Time-domain plots
# ==================================================
st.subheader("Photon Signal (TESS Flux)")
st.line_chart(results["x"], height=260)

st.subheader("Core Variables")
st.line_chart(results[["Sigma", "Z", "G"]], height=320)

st.subheader("Phase Scores")
st.line_chart(results[["Phase0_score", "Release_score"]], height=260)

st.subheader("Phase Markers Overlay")
overlay = pd.DataFrame(index=results.index)
overlay["signal"] = results["x"]
overlay["Phase-0"] = results["x"].where(results["Phase0"])
overlay["Release"] = results["x"].where(results["Release"])
st.line_chart(overlay, height=320)

# ==================================================
# Sandy’s Square — Σ vs Z
# ==================================================
st.subheader("Sandy’s Square (Σ vs Z)")

square_df = results[["Z", "Sigma", "Regime", "Phase0", "Release"]].dropna()

color_map = {
    "Trapped": "#1f77b4",
    "Transitional": "#ff7f0e",
    "Escaping": "#2ca02c",
}

colors = square_df["Regime"].map(color_map).fillna("#7f7f7f")

fig, ax = plt.subplots(figsize=(7, 7))

ax.scatter(
    square_df["Z"],
    square_df["Sigma"],
    c=colors,
    s=6,
    alpha=0.35,
    linewidths=0
)

# Phase-0 markers
p0 = square_df[square_df["Phase0"]]
ax.scatter(
    p0["Z"],
    p0["Sigma"],
    facecolors="none",
    edgecolors="black",
    s=30,
    linewidths=0.8,
    label="Phase-0"
)

# Release markers
rel = square_df[square_df["Release"]]
ax.scatter(
    rel["Z"],
    rel["Sigma"],
    c="red",
    s=18,
    marker="x",
    label="Release"
)

ax.set_xlabel("Z — Structural Constraint (Trap Strength)")
ax.set_ylabel("Σ — Information Density")
ax.set_title("Sandy’s Square: Structural State Space")

ax.set_xlim(0, 1)
ax.set_ylim(0, square_df["Sigma"].max() * 1.05)

ax.grid(True, alpha=0.3)
ax.legend(frameon=False)

st.pyplot(fig)

# ==================================================
# Export
# ==================================================
st.subheader("Export Results")

st.download_button(
    "Download full Sandy’s Square results (CSV)",
    data=results.to_csv(index=False),
    file_name=f"{target.replace(' ','_')}_sandys_square_tess.csv",
    mime="text/csv"
)

st.caption(
    "Real TESS photon data processed through Sandy’s Square. "
    "Σ = information density, Z = trapping/constraint, "
    "G = escape gate, Phase-0 = trapped precursor."
)
# Fetch TESS light curve
# ==================================================
with st.spinner("Fetching TESS photon data…"):
    try:
        search = lk.search_lightcurve(
            target,
            mission="TESS",
            cadence=cadence
        )

        if len(search) == 0:
            st.error("No TESS light curve found for this target.")
            st.stop()

        lc = search.download().PDCSAP_FLUX

    except Exception as e:
        st.error(f"TESS fetch failed: {e}")
        st.stop()

# ==================================================
# SAFE conversion: Astropy → NumPy → DataFrame
# ==================================================
try:
    t = np.asarray(lc.time.value, dtype=np.float64)
    x = np.asarray(lc.flux.value, dtype=np.float64)
except Exception as e:
    st.error(f"Data conversion failed: {e}")
    st.stop()

mask = np.isfinite(t) & np.isfinite(x)
df = pd.DataFrame({
    "t": t[mask],
    "x": x[mask]
}).reset_index(drop=True)

if df.empty:
    st.error("All data points were invalid after cleaning.")
    st.stop()

if len(df) < win + slope_win + 5:
    st.warning(
        f"Only {len(df)} data points available. "
        f"Reduce window sizes for stable results."
    )

# ==================================================
# Run Sandy’s Square / SLED
# ==================================================
features = compute_sled_features(
    df,
    win=win,
    entropy_bins=entropy_bins
)

results = sled_detect(
    features,
    slope_win=slope_win,
    z_high=z_high,
    z_stable_max_std=z_stable,
    sigma_slope_min=sigma_slope_min,
    z_drop_min=z_drop_min,
    g_rise_min=g_rise_min,
    r_spike_q=r_spike_q,
)

# ==================================================
# Summary
# ==================================================
st.subheader("Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Data points", len(results))
c2.metric("Phase-0 count", int(results["Phase0"].sum()))
c3.metric("Release count", int(results["Release"].sum()))
c4.metric("Final regime", results["Regime"].iloc[-1])

# ==================================================
# Visualisations
# ==================================================
st.subheader("Photon Signal (TESS Flux)")
st.line_chart(results["x"], height=260)

st.subheader("Sandy’s Square Core Variables")
st.line_chart(results[["Sigma", "Z", "G"]], height=320)

st.subheader("Phase Scores")
st.line_chart(results[["Phase0_score", "Release_score"]], height=260)

st.subheader("Phase Markers Overlay")
overlay = pd.DataFrame(index=results.index)
overlay["signal"] = results["x"]
overlay["Phase-0"] = results["x"].where(results["Phase0"])
overlay["Release"] = results["x"].where(results["Release"])
st.line_chart(overlay, height=320)

# ==================================================
# Export
# ==================================================
st.subheader("Export Results")

st.download_button(
    "Download full Sandy’s Square results (CSV)",
    data=results.to_csv(index=False),
    file_name=f"{target.replace(' ','_')}_sandys_square_tess.csv",
    mime="text/csv"
)

st.caption(
    "Real TESS photon data processed through Sandy’s Square. "
    "Σ = internal information density, Z = trapping/constraint, "
    "G = escape gate, Phase-0 = trapped precursor."
)
