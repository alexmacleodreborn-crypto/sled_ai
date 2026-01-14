import streamlit as st
import pandas as pd
import io

from sled.io import load_csv
from sled.features import compute_sled_features
from sled.detector import sled_detect

# ==================================================
# Page config
# ==================================================
st.set_page_config(
    page_title="SLED AI — Full Instrument",
    layout="wide"
)

st.title("SLED AI — Full Structural Observability Instrument")
st.caption(
    "Full SLED v1.0: Σ (entropy), Z (constraint), G (gate), "
    "Phase-0 score, Release score, Regime labels"
)

# ==================================================
# Session state
# ==================================================
if "run_sled" not in st.session_state:
    st.session_state.run_sled = False

# ==================================================
# Sidebar parameters
# ==================================================
with st.sidebar:
    st.header("Core Windows")

    win = st.slider(
        "Feature window (Σ, O, Z, G)",
        min_value=16,
        max_value=256,
        value=64,
        step=8,
    )

    entropy_bins = st.slider(
        "Entropy bins (Σ)",
        min_value=8,
        max_value=64,
        value=16,
        step=4,
    )

    slope_win = st.slider(
        "Slope / stability window",
        min_value=6,
        max_value=64,
        value=12,
        step=1,
    )

    st.divider()
    st.header("Phase-0 Thresholds")

    z_high = st.slider(
        "High-constraint threshold (Z high)",
        min_value=0.50,
        max_value=0.95,
        value=0.70,
        step=0.01,
    )

    z_stable = st.slider(
        "Constraint stability (Z std max)",
        min_value=0.01,
        max_value=0.25,
        value=0.08,
        step=0.01,
    )

    sigma_slope_min = st.slider(
        "Minimum Σ slope",
        min_value=-0.10,
        max_value=0.20,
        value=0.00,
        step=0.01,
    )

    st.divider()
    st.header("Release Thresholds")

    z_drop_min = st.slider(
        "Minimum Z drop (ΔZ)",
        min_value=0.01,
        max_value=0.50,
        value=0.10,
        step=0.01,
    )

    g_rise_min = st.slider(
        "Minimum G rise (ΔG)",
        min_value=0.01,
        max_value=1.00,
        value=0.10,
        step=0.01,
    )

    r_spike_q = st.slider(
        "Return spike quantile",
        min_value=0.50,
        max_value=0.99,
        value=0.95,
        step=0.01,
    )

    st.divider()
    st.header("Regime Labels")

    z_trapped = st.slider(
        "Trapped if Z ≥",
        min_value=0.50,
        max_value=0.98,
        value=0.75,
        step=0.01,
    )

    z_open = st.slider(
        "Escaping if Z ≤",
        min_value=0.02,
        max_value=0.60,
        value=0.35,
        step=0.01,
    )

# ==================================================
# CSV paste input
# ==================================================
st.subheader("Paste CSV Data")

csv_text = st.text_area(
    "Paste CSV here (must contain two columns: time,value)",
    height=240,
    placeholder="time,value\n0,100\n1,100.1\n2,100.05\n3,100.1\n4,100.15\n5,101.8",
)

st.caption("Accepted column names: time / timestamp / t and value / x / price")

colA, colB = st.columns(2)
with colA:
    if st.button("Run SLED"):
        st.session_state.run_sled = True
with colB:
    if st.button("Reset"):
        st.session_state.run_sled = False

# ==================================================
# Gate execution
# ==================================================
if not st.session_state.run_sled:
    st.info("⬆️ Paste CSV data above and click **Run SLED**.")
    st.stop()

if not csv_text.strip():
    st.error("Please paste CSV data before running SLED.")
    st.stop()

# ==================================================
# Parse CSV
# ==================================================
try:
    df_raw = pd.read_csv(io.StringIO(csv_text))
except Exception as e:
    st.error(f"CSV parse error: {e}")
    st.stop()

if df_raw.shape[1] < 2:
    st.error("CSV must contain at least two columns.")
    st.stop()

df = load_csv(io.StringIO(csv_text))
df = df.dropna()

if df.empty or df.shape[0] < max(win, slope_win) + 5:
    st.warning(
        f"Dataset has {df.shape[0]} rows. "
        f"For stable SLED output, use at least ~{max(win, slope_win) + 5} rows "
        f"or reduce the windows."
    )

# ==================================================
# Compute features + full detection
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
    z_trapped=z_trapped,
    z_open=z_open,
)

# ==================================================
# Summary
# ==================================================
st.subheader("Summary")

phase0_count = int(results["Phase0"].fillna(False).sum())
release_count = int(results["Release"].fillna(False).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", len(results))
c2.metric("Phase-0 flags", phase0_count)
c3.metric("Release flags", release_count)
c4.metric("Last regime", str(results["Regime"].iloc[-1]))

# ==================================================
# Results table
# ==================================================
st.subheader("Results Preview")

cols = [
    "t", "x", "Sigma", "O", "Z", "G",
    "Phase0_score", "Phase0",
    "Release_score", "Release",
    "Regime"
]
st.dataframe(results[cols].tail(40), use_container_width=True)

# ==================================================
# Charts
# ==================================================
st.subheader("Signal (x)")
st.line_chart(results["x"], height=260)

st.subheader("Core SLED Variables")
st.line_chart(results[["Sigma", "Z", "G"]], height=320)

st.subheader("Scores")
st.line_chart(results[["Phase0_score", "Release_score"]], height=260)

st.subheader("Phase Markers Overlay")
overlay = pd.DataFrame(index=results.index)
overlay["signal"] = results["x"]
overlay["Phase0"] = results["x"].where(results["Phase0"].fillna(False))
overlay["Release"] = results["x"].where(results["Release"].fillna(False))
st.line_chart(overlay, height=320)

# ==================================================
# Export
# ==================================================
st.subheader("Export Results")

csv_out = results.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download results as CSV",
    data=csv_out,
    file_name="sled_full_results.csv",
    mime="text/csv",
)

st.caption(
    "SLED AI — Full structural instrument. "
    "Σ: entropy of returns, O: observability proxy, Z: constraint, G: gate output. "
    "Phase-0 is a trapped precursor; Release indicates escape."
)
