import streamlit as st
import pandas as pd
import io

from sled.io import load_csv
from sled.features import compute_sled_features
from sled.detector import phase0_flags

# ==================================================
# Page config
# ==================================================
st.set_page_config(
    page_title="SLED AI — Phase-0 Detector",
    layout="wide"
)

st.title("SLED AI — Structural Observability & Phase-0 Detection")
st.caption(
    "Reference implementation of the SLED method from "
    "“A Structural Information Framework for Trapped, Transitional, and Escaping Systems”"
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
    st.header("SLED Parameters")

    win = st.slider(
        "Feature window (Σ, Z)",
        min_value=16,
        max_value=256,
        value=64,
        step=8,
    )

    slope_win = st.slider(
        "Sigma slope window",
        min_value=6,
        max_value=64,
        value=12,
        step=1,
    )

    z_high = st.slider(
        "High-constraint threshold (Z)",
        min_value=0.50,
        max_value=0.95,
        value=0.75,
        step=0.01,
    )

    z_stable = st.slider(
        "Constraint stability (Z std max)",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01,
    )

    sigma_slope_min = st.slider(
        "Minimum Σ slope",
        min_value=-0.10,
        max_value=0.20,
        value=0.00,
        step=0.01,
    )

# ==================================================
# CSV paste input
# ==================================================
st.subheader("Paste CSV Data")

csv_text = st.text_area(
    "Paste CSV here (must contain two columns: time,value)",
    height=220,
    placeholder="time,value\n0,100\n1,100.1\n2,100.05\n3,100.1\n4,100.15\n5,101.8",
)

st.caption(
    "Accepted column names: time / timestamp / t and value / x / price"
)

if st.button("Run SLED"):
    st.session_state.run_sled = True

# ==================================================
# Gate execution properly
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

# Normalize columns using existing loader
df = load_csv(io.StringIO(csv_text))

if df.empty or df.isna().all().any():
    st.error("Parsed data is empty or invalid.")
    st.stop()

# ==================================================
# Compute SLED features
# ==================================================
features = compute_sled_features(df, win=win)

results = phase0_flags(
    features,
    slope_win=slope_win,
    z_high=z_high,
    z_stable_max_std=z_stable,
    sigma_slope_min=sigma_slope_min,
)

# ==================================================
# Output preview
# ==================================================
st.subheader("Results Preview")
st.dataframe(
    results.tail(30),
    use_container_width=True
)

# ==================================================
# Visualizations (Streamlit native)
# ==================================================
st.subheader("Signal")
st.line_chart(results["x"], height=250)

st.subheader("SLED Features (Σ, Z, G)")
st.line_chart(results[["Sigma", "Z", "G"]], height=300)

# ==================================================
# Phase-0 detection
# ==================================================
phase0_idx = results.index[results["Phase0"].fillna(False)]

st.subheader("Phase-0 Detection")

if len(phase0_idx) > 0:
    st.success(f"Phase-0 detected at {len(phase0_idx)} points.")
    st.line_chart(
        pd.DataFrame({
            "signal": results["x"],
            "phase0": results["x"].where(results["Phase0"])
        }),
        height=300
    )
else:
    st.warning("No Phase-0 states detected under current parameters.")

# ==================================================
# Export
# ==================================================
st.subheader("Export Results")

csv_out = results.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download results as CSV",
    data=csv_out,
    file_name="sled_results.csv",
    mime="text/csv",
)

# ==================================================
# Footer
# ==================================================
st.caption(
    "SLED AI — illustrative reference implementation. "
    "Structural analysis, not domain-optimized."
)
