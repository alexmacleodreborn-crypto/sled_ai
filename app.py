import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Optional: Lightkurve for TESS mode
try:
    import lightkurve as lk
    LIGHTKURVE_OK = True
except Exception:
    LIGHTKURVE_OK = False

from sled.features import compute_sled_features
from sled.detector import sled_detect


# ==================================================
# Helpers
# ==================================================
def mag_to_flux(mag: np.ndarray, mag0: float | None = None) -> np.ndarray:
    """
    Convert magnitude to a relative flux proxy:
      F ~ 10^(-0.4*(mag - mag0))
    mag0 defaults to median(mag) for numeric stability.
    """
    mag = np.asarray(mag, dtype=np.float64)
    if mag0 is None or not np.isfinite(mag0):
        mag0 = float(np.nanmedian(mag))
    return 10.0 ** (-0.4 * (mag - mag0))


def clean_two_columns(df: pd.DataFrame, tcol: str, vcol: str) -> pd.DataFrame:
    t = pd.to_numeric(df[tcol], errors="coerce")
    v = pd.to_numeric(df[vcol], errors="coerce")
    out = pd.DataFrame({"t": t, "v": v}).dropna()
    out = out[np.isfinite(out["t"]) & np.isfinite(out["v"])]
    out = out.sort_values("t").reset_index(drop=True)
    return out


def safe_line_chart(df_or_series, height=260):
    try:
        st.line_chart(df_or_series, height=height)
    except Exception:
        st.write(df_or_series)


# ==================================================
# Page config
# ==================================================
st.set_page_config(page_title="Sandy’s Square — TESS + Supernova", layout="wide")
st.title("Sandy’s Square — Observability State Space")
st.caption("One engine • multiple domains: Supernova light curves (CSV) and TESS photons (Lightkurve optional)")


# ==================================================
# Mode selector
# ==================================================
mode = st.selectbox("Data source", ["Supernova (CSV)", "TESS (Lightkurve)"], index=0)


# ==================================================
# Sidebar parameters
# ==================================================
with st.sidebar:
    st.header("Sandy’s Square Parameters")

    # Defaults that work better for small SN datasets (like 26 points)
    default_win = 16 if mode == "Supernova (CSV)" else 64
    default_slope_win = 6 if mode == "Supernova (CSV)" else 12
    default_bins = 8 if mode == "Supernova (CSV)" else 16

    win = st.slider("Feature window (win)", 8, 256, default_win, 2)
    entropy_bins = st.slider("Entropy bins (Σ)", 4, 64, default_bins, 1)
    slope_win = st.slider("Slope window", 3, 64, default_slope_win, 1)

    st.divider()

    z_high = st.slider("Z high (Phase-0 threshold)", 0.50, 0.95, 0.70, 0.01)
    z_stable = st.slider("Z stability (std max)", 0.01, 0.25, 0.08, 0.01)
    sigma_slope_min = st.slider("Min Σ slope", -0.10, 0.20, 0.00, 0.01)

    z_drop_min = st.slider("Min ΔZ (release)", 0.01, 0.50, 0.10, 0.01)
    g_rise_min = st.slider("Min ΔG (release)", 0.01, 1.00, 0.10, 0.01)
    r_spike_q = st.slider("Return spike quantile", 0.50, 0.99, 0.95, 0.01)

    st.divider()
    st.header("Square Trajectory")
    arrow_density = st.slider("Arrow density (higher = fewer arrows)", 80, 800, 250, 10)


# ==================================================
# Ingestion
# ==================================================
df = None
meta_label = ""


if mode == "TESS (Lightkurve)":
    if not LIGHTKURVE_OK:
        st.error("Lightkurve not installed. Add `lightkurve` to requirements.txt, or use Supernova (CSV) mode.")
        st.stop()

    with st.sidebar:
        st.header("TESS Settings")
        target = st.text_input("TIC or target", value="TIC 307210830")
        cadence = st.selectbox("Cadence", ["short", "long"], index=0)
        run = st.button("Fetch TESS & Run")

    if not run:
        st.info("⬅️ Choose TESS settings and click **Fetch TESS & Run**.")
        st.stop()

    with st.spinner("Fetching TESS data…"):
        try:
            search = lk.search_lightcurve(target, mission="TESS", cadence=cadence)
            if len(search) == 0:
                st.error("No TESS light curve found for this target.")
                st.stop()

            lc = search.download().PDCSAP_FLUX

            # Safe conversion (astropy → numpy)
            t = np.asarray(lc.time.value, dtype=np.float64)
            x = np.asarray(lc.flux.value, dtype=np.float64)
            mask = np.isfinite(t) & np.isfinite(x)

            df = pd.DataFrame({"t": t[mask], "x": x[mask]}).reset_index(drop=True)
            meta_label = f"TESS: {target} ({cadence})"
        except Exception as e:
            st.error(f"TESS fetch failed: {e}")
            st.stop()

else:
    st.subheader("Supernova (CSV) Input")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])

    with col2:
        pasted = st.text_area(
            "Or paste CSV text",
            height=180,
            placeholder="time,mag,band\n57822.56,15.488,B\n..."
        )

    if uploaded is None and not pasted.strip():
        st.info("Upload a CSV or paste CSV text to continue.")
        st.stop()

    # Read CSV
    try:
        if uploaded is not None:
            raw = pd.read_csv(uploaded)
            meta_label = f"SN CSV: {uploaded.name}"
        else:
            from io import StringIO
            raw = pd.read_csv(StringIO(pasted))
            meta_label = "SN CSV: pasted"
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        st.stop()

    st.write("Preview", raw.head())

    # Column choices
    cols = list(raw.columns)
    time_col = st.selectbox("Time column", cols, index=cols.index("time") if "time" in cols else 0)

    # value candidates
    preferred = None
    for c in ["mag", "magnitude", "flux", "x", "value"]:
        if c in cols:
            preferred = c
            break
    value_col = st.selectbox("Value column (mag or flux)", cols, index=cols.index(preferred) if preferred in cols else 1)

    # Band support (optional)
    band_col = None
    if "band" in cols:
        band_col = "band"
    elif "filter" in cols:
        band_col = "filter"

    if band_col is not None:
        bands = sorted([b for b in raw[band_col].dropna().unique()])
        chosen_band = st.selectbox("Band (optional but recommended)", ["(all)"] + bands, index=0)
        if chosen_band != "(all)":
            raw = raw[raw[band_col] == chosen_band].copy()
            meta_label += f" | band={chosen_band}"

    value_type = st.selectbox("Value type", ["mag", "flux"], index=0 if "mag" in value_col.lower() else 1)

    # Clean and map to df(t,x)
    cleaned = clean_two_columns(raw, time_col, value_col)
    if cleaned.empty:
        st.error("No valid numeric rows after cleaning.")
        st.stop()

    t = cleaned["t"].to_numpy(dtype=np.float64)
    v = cleaned["v"].to_numpy(dtype=np.float64)

    if value_type == "mag":
        x = mag_to_flux(v, mag0=float(np.nanmedian(v)))
    else:
        x = v

    # mild normalization (keeps shapes but stabilizes numerics)
    med = np.nanmedian(x)
    if np.isfinite(med) and med != 0:
        x = x / med

    df = pd.DataFrame({"t": t, "x": x}).reset_index(drop=True)

    with st.expander("Cleaned SN series (first/last)", expanded=False):
        st.write(df.head())
        st.write(df.tail())


# ==================================================
# Safety checks
# ==================================================
if df is None or df.empty:
    st.error("No data to process.")
    st.stop()

if len(df) < win + slope_win + 3:
    st.warning(
        f"Only {len(df)} points available. "
        f"Consider smaller win/slope_win (e.g., win=12–24, slope_win=4–8 for sparse SN data)."
    )


# ==================================================
# Run Sandy’s Square engine
# ==================================================
features = compute_sled_features(df, win=win, entropy_bins=entropy_bins)

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
st.caption(meta_label)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", len(results))
c2.metric("Phase-0", int(results["Phase0"].fillna(False).sum()))
c3.metric("Release", int(results["Release"].fillna(False).sum()))
c4.metric("Final regime", str(results["Regime"].iloc[-1]))


# ==================================================
# Time-domain plots
# ==================================================
st.subheader("Signal (x)")
safe_line_chart(results["x"], height=240)

st.subheader("Core variables (Σ, Z, G)")
safe_line_chart(results[["Sigma", "Z", "G"]], height=320)

st.subheader("Phase scores")
safe_line_chart(results[["Phase0_score", "Release_score"]], height=240)

st.subheader("Markers overlay")
overlay = pd.DataFrame(index=results.index)
overlay["signal"] = results["x"]
overlay["Phase-0"] = results["x"].where(results["Phase0"].fillna(False))
overlay["Release"] = results["x"].where(results["Release"].fillna(False))
safe_line_chart(overlay, height=320)


# ==================================================
# Sandy’s Square (Σ vs Z) + direction arrows
# ==================================================
st.subheader("Sandy’s Square (Σ vs Z)")

square_df = results[["Z", "Sigma", "Regime", "Phase0", "Release"]].dropna().reset_index(drop=True)

color_map = {"Trapped": "#1f77b4", "Transitional": "#ff7f0e", "Escaping": "#2ca02c"}
colors = square_df["Regime"].map(color_map).fillna("#7f7f7f")

fig, ax = plt.subplots(figsize=(7.5, 7.5))

ax.scatter(
    square_df["Z"],
    square_df["Sigma"],
    c=colors,
    s=10 if mode == "Supernova (CSV)" else 6,
    alpha=0.35,
    linewidths=0
)

# Direction arrows (subsample)
step = max(len(square_df) // max(int(arrow_density), 1), 1)
Zs = square_df["Z"].values
Ss = square_df["Sigma"].values

for i in range(0, len(square_df) - step, step):
    ax.arrow(
        Zs[i],
        Ss[i],
        Zs[i + step] - Zs[i],
        Ss[i + step] - Ss[i],
        length_includes_head=True,
        head_width=0.010 if mode == "Supernova (CSV)" else 0.008,
        head_length=0.020 if mode == "Supernova (CSV)" else 0.015,
        fc="black",
        ec="black",
        alpha=0.25
    )

# Phase-0 markers
p0 = square_df[square_df["Phase0"]]
ax.scatter(
    p0["Z"], p0["Sigma"],
    facecolors="none",
    edgecolors="black",
    s=60 if mode == "Supernova (CSV)" else 30,
    linewidths=1.0,
    label="Phase-0"
)

# Release markers
rel = square_df[square_df["Release"]]
ax.scatter(
    rel["Z"], rel["Sigma"],
    c="red",
    s=45 if mode == "Supernova (CSV)" else 22,
    marker="x",
    label="Release"
)

ax.set_xlabel("Z — Structural Constraint (Trap Strength)")
ax.set_ylabel("Σ — Information Density")
ax.set_title("Sandy’s Square: Structural State Space")

ax.set_xlim(0, 1)
ax.set_ylim(0, max(1e-9, float(square_df["Sigma"].max()) * 1.05))
ax.grid(True, alpha=0.3)
ax.legend(frameon=False)

st.pyplot(fig)


# ==================================================
# Export
# ==================================================
st.subheader("Export")
st.download_button(
    "Download results (CSV)",
    data=results.to_csv(index=False),
    file_name=f"{meta_label.replace(' ', '_').replace(':','')}_sandys_square.csv",
    mime="text/csv",
    key="square_csv_download"
)
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
t = np.asarray(lc.time.value, dtype=np.float64)
x = np.asarray(lc.flux.value, dtype=np.float64)

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
# Sandy’s Square — Σ vs Z with trajectory
# ==================================================
st.subheader("Sandy’s Square (Σ vs Z)")

square_df = results[["Z", "Sigma", "Regime", "Phase0", "Release"]].dropna().reset_index(drop=True)

color_map = {
    "Trapped": "#1f77b4",
    "Transitional": "#ff7f0e",
    "Escaping": "#2ca02c",
}
colors = square_df["Regime"].map(color_map).fillna("#7f7f7f")

fig, ax = plt.subplots(figsize=(7.5, 7.5))

ax.scatter(
    square_df["Z"],
    square_df["Sigma"],
    c=colors,
    s=6,
    alpha=0.30,
    linewidths=0
)

# Trajectory arrows (adaptive subsampling)
step = max(len(square_df) // 300, 1)
Zs = square_df["Z"].values
Ss = square_df["Sigma"].values

for i in range(0, len(square_df) - step, step):
    ax.arrow(
        Zs[i],
        Ss[i],
        Zs[i + step] - Zs[i],
        Ss[i + step] - Ss[i],
        length_includes_head=True,
        head_width=0.008,
        head_length=0.015,
        fc="black",
        ec="black",
        alpha=0.25
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
    s=22,
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
    mime="text/csv",
    key="square_csv_download"
)

st.caption(
    "Real TESS photon data processed through Sandy’s Square. "
    "Σ = information density, Z = trapping/constraint, "
    "G = escape gate, Phase-0 = trapped precursor."
)
