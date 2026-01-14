import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Sandy’s Law — Persistence (LRD)",
    layout="wide"
)

st.title("Sandy’s Law — Persistence (Low-Radiance Domain)")
st.caption(
    "Demonstration of structural persistence using real supernova photometry "
    "(energy present, observability suppressed)"
)

# --------------------------------------------------
# Sidebar navigation (NOT pages)
# --------------------------------------------------
view = st.sidebar.radio(
    "View",
    [
        "Persistence (Low-Radiance Domain)",
        "Structural State Space (Square)"
    ]
)

# --------------------------------------------------
# Data upload (required)
# --------------------------------------------------
st.sidebar.header("Data Input")

uploaded = st.sidebar.file_uploader(
    "Upload SN B-band CSV (time, mag)",
    type=["csv"]
)

if uploaded is None:
    st.info(
        "⬅️ Upload `SN2017cbv_B.csv` to begin.\n\n"
        "The CSV must contain columns:\n"
        "`time, mag`"
    )
    st.stop()

# --------------------------------------------------
# Read and validate CSV
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

df = df[["time", "mag"]].dropna()
df = df.sort_values("time").reset_index(drop=True)

# --------------------------------------------------
# VIEW 1 — PERSISTENCE / LRD
# --------------------------------------------------
if view == "Persistence (Low-Radiance Domain)":

    st.header("Persistence / Low-Radiance Domain (LRD)")

    st.markdown(
        """
**Persistence** is a regime where energy exists and evolves internally,
but observable radiation remains suppressed due to strong structural
constraints.

In this regime:
- Energy ≠ observability
- Photons exist but are mass-coupled and trapped
- Observable information does not accumulate

The light curve below shows this directly.
"""
    )

    # Plot light curve
    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.plot(
        df["time"],
        df["mag"],
        marker="o",
        linestyle="-",
        color="black"
    )

    ax.invert_yaxis()
    ax.set_xlabel("Time (MJD)")
    ax.set_ylabel("B-band Magnitude")
    ax.set_title("SN2017cbv — B-band Light Curve")

    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    st.info(
        "Early times show minimal observable change despite ongoing internal "
        "energy production. This silent interval is the **Persistence / "
        "Low-Radiance Domain**."
    )

    st.markdown(
        """
**Key point:**  
The supernova does not become visible when energy is created.  
It becomes visible when **structural constraints weaken and photon escape becomes permitted**.
"""
    )

# --------------------------------------------------
# VIEW 2 — STRUCTURAL STATE SPACE (LOCKED FOR NOW)
# --------------------------------------------------
else:

    st.header("Structural State Space (Sandy’s Square)")

    st.warning(
        "The Square is intentionally disabled at this stage.\n\n"
        "Persistence (Low-Radiance Domain) must be established first.\n\n"
        "Next steps will:\n"
        "- introduce event-scaled observable information (Σ)\n"
        "- define structural constraint (Z)\n"
        "- show boundary crossing as photon release"
    )

    st.markdown(
        """
This ordering is deliberate.

The Square is **not a discovery tool**.  
It is a **map of consequences** once Persistence is understood.
"""
    )

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption(
    "Sandy’s Law — Persistence Demonstration | "
    "CSV-based • Deterministic • Reproducible"
)
