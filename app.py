import streamlit as st
import pandas as pd
import io

from sled.io import load_csv
from sled.features import compute_sled_features
from sled.detector import phase0_flags

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="SLED AI — Phase-0 Detector",
    layout="wide"
)

st.title("SLED AI — Structural Observability & Phase-0 Detection")
st.caption(
    "Reference implementation of the SLED method from "
    "“A Structural Information Framework for Trapped, Transitional, and Escaping Systems”"
)

# --------------------------------------------------
# Sidebar parameters
# --------------------------------------------------
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

# --------------------------------------------------
# CSV paste input
# --------------------------------------------------
st.subheader("Paste CSV Data")

csv_text = st.text_area(
    "Paste CSV here (must contain two columns: time,value)",
    height=220,
    placeholder="time,value\n0,100\n1,100.1\n2,100.05\n3,100.2\n4,101.5",
)

st.caption(
    "Accepted column names: time / timestamp / t and value / x / price"
)

run = st.button("Run SLED")

if not run:
    st.stop()

if not csv_text.strip():
    st.error("Please paste CSV data before running SLED.")
    st.stop()

# --------------------------------------------------
# Parse CSV
# --------------------------------------------------
try:
    df_raw = pd.read_csv(io.StringIO(csv_text))
except Exception as e:
    st.error(f"CSV parse error: {e}")
    st.stop()

# Reuse loader logic for column normalization
df = load_csv(io.StringIO(csv_text))

# --------------------------------------------------
# Compute SLED features
# --------------------------------------------------
features = compute_sled_features(df, win=win)

results = phase0_flags(
    features,
    slope_win=slope_win,
    z_high=z_high,
    z_stable_max_std=z_stable,
    sigma_slope_min=sigma_slope_min,
)

# --------------------------------------------------
# Output preview
# --------

