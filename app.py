import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Sandy’s Law — Persistence Demonstration")

page = st.sidebar.radio(
    "View",
    ["Persistence (Low-Radiance Domain)", "Structural State Space (Square)"]
)

df = pd.read_csv("data/SN2017cbv_B.csv")

if page == "Persistence (Low-Radiance Domain)":
    st.header("Persistence / Low-Radiance Domain")

    st.markdown("""
    **Persistence** is a regime where energy exists but observability is suppressed
    by structural constraints. The light curve below shows early supernova activity
    without significant photon escape.
    """)

    fig, ax = plt.subplots()
    ax.plot(df["time"], df["mag"], marker="o")
    ax.invert_yaxis()
    ax.set_xlabel("Time (MJD)")
    ax.set_ylabel("B-band Magnitude")
    ax.set_title("SN2017cbv — B-band Light Curve")
    st.pyplot(fig)

    st.info(
        "Early times show minimal observable change despite ongoing internal energy production. "
        "This is the Persistence (Low-Radiance) regime."
    )

else:
    st.header("Structural State Space (Sandy’s Square)")
    st.markdown(
        "This page maps observability (Σ) against structural constraint (Z). "
        "It will be enabled after the Persistence regime is established."
    )
    st.warning("Square implementation intentionally follows Persistence.")
