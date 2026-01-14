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

# --------------------------------------------------
# Observable Information Σ (event-scaled)
# --------------------------------------------------

# Convert magnitude to relative flux proxy
m0 = df["mag"].iloc[0]
df["flux_proxy"] = 10 ** (-0.4 * (df["mag"] - m0))

# Incremental observable change
df["delta_flux"] = df["flux_proxy"].diff().abs().fillna(0.0)

# Cumulative observable information
df["Sigma"] = df["delta_flux"].cumsum()

# Normalised Sigma for plotting
df["Sigma_norm"] = df["Sigma"] / df["Sigma"].max() if df["Sigma"].max() > 0 else 0

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
    # Light curve
    # --------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.plot(
        df["time"],
        df["mag"],
        marker="o",
        linestyle="-",
        color="black"
    )

    ax.invert_yaxis()
    ax.set_xlabel("Time")
    ax.set_ylabel("B-band Magnitude")
    ax.set_title("Supernova B-band Light Curve")

    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    st.info(
        "Early times show minimal observable change despite ongoing internal "
        "energy production. This silent interval is described by **Mag’s Law** "
        "and corresponds to the **Low-Radiance Domain**."
    )

    # --------------------------------------------------
    # Observable Information Σ
    # --------------------------------------------------
    st.subheader("Observable Information Accumulation (Σ)")

    st.markdown(
        """
Σ (Sigma) is a **proxy for observable information**, defined here as the
cumulative magnitude of observed change in the signal.

This definition is:
- event-scaled (no sliding windows)
- robust to sparse, irregular sampling
- appropriate for supernova light curves
"""
    )

    fig2, ax2 = plt.subplots(figsize=(9, 4))

    ax2.plot(
        df["time"],
        df["Sigma_norm"],
        marker="o",
        linestyle="-",
        color="tab:blue"
    )

    ax2.set_xlabel("Time")
    ax2.set_ylabel("Normalised Σ")
    ax2.set_title("Cumulative Observable Information (Σ)")

    ax2.grid(True, alpha=0.3)

    st.pyplot(fig2)

    st.success(
        "During Mag’s Law (Persistence), Σ remains near-flat.\n"
        "Σ rises rapidly only when structural constraints weaken "
        "and photon escape becomes permitted."
    )

    st.markdown(
        """
**Key point (Mag’s Law):**  
A system does not become visible when energy is created.  
It becomes visible when **observable information begins to accumulate**.
"""
    )

# --------------------------------------------------
# VIEW 2 — SANDY’S SQUARE (STILL LOCKED)
# --------------------------------------------------
else:

    st.header("Structural State Space (Sandy’s Square)")

    st.warning(
        "Sandy’s Square is intentionally disabled at this stage.\n\n"
        "Now that Σ (observable information) is defined, the next step will be:\n"
        "- defining structural constraint (Z)\n"
        "- mapping (Z, Σ) trajectories\n"
        "- identifying boundary crossing from Mag’s Law to release"
    )

    st.markdown(
        """
The Square is a **map of consequences**, not a discovery engine.

It becomes meaningful only after Mag’s Law (Persistence)
and observable information (Σ) are established.
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
