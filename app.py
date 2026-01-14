import streamlit as st
import pandas as pd
import lightkurve as lk

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
    "Live TESS photon data → Σ–Z Square → Phase-0 → Escape"
)

# ==================================================
# Sidebar — TESS controls
# ==================================================
with st.sidebar:
    st.header("TESS Target")

    target = st.text_input(
        "TIC ID or target name",
        value="TIC 307210830",
        help="Example: TIC 307210830 (bright, well-sampled)"
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
# Fetch TESS data
# ==================================================
if not run:
    st.info("⬅️ Enter a TESS target and click **Fetch TESS & Run**")
    st.stop()

with st.spinner("Fetching TESS photon data…"):
    try:
        search = lk.search_lightcurve(
            target,
            mission="TESS",
            cadence=cadence
        )
        if len(search) == 0:
            st.error("No TESS data found for this target.")
            st.stop()

        lc = search.download().PDCSAP_FLUX
    except Exception as e:
        st.error(f"TESS fetch failed: {e}")
        st.stop()

# ==================================================
# Convert to Sandy’s Square format
# ==================================================
df = pd.DataFrame({
    "t": lc.time.value,
    "x": lc.flux.value
}).dropna().reset_index(drop=True)

if len(df) < win + slope_win + 5:
    st.warning(
        f"Only {len(df)} points available. "
        f"Consider reducing the window sizes."
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
# Plots
# ==================================================
st.subheader("Photon Signal (TESS flux)")
st.line_chart(results["x"], height=260)

st.subheader("Sandy’s Square Core Variables")
st.line_chart(results[["Sigma", "Z", "G"]], height=320)

st.subheader("Phase Scores")
st.line_chart(results[["Phase0_score", "Release_score"]], height=260)

st.subheader("Square Overlay (Markers)")
overlay = pd.DataFrame(index=results.index)
overlay["signal"] = results["x"]
overlay["Phase-0"] = results["x"].where(results["Phase0"])
overlay["Release"] = results["x"].where(results["Release"])
st.line_chart(overlay, height=320)

# ==================================================
# Export
# ==================================================
st.subheader("Export")

st.download_button(
    "Download full results CSV",
    data=results.to_csv(index=False),
    file_name=f"{target.replace(' ','_')}_sandys_square_tess.csv",
    mime="text/csv"
)

st.caption(
    "This is real TESS photon data processed through Sandy’s Square. "
    "Σ = internal information density, Z = photon trapping, "
    "G = escape gate, Phase-0 = trapped precursor."
)
