import streamlit as st
import matplotlib.pyplot as plt

from sled.io import load_csv
from sled.features import compute_sled_features
from sled.detector import phase0_flags

st.set_page_config(page_title="SLED AI", layout="wide")
st.title("SLED AI — Phase-0 Detector")

uploaded = st.file_uploader("Upload CSV (time,value)", type=["csv"])

with st.sidebar:
    win = st.slider("Feature window", 16, 256, 64, 8)
    slope_win = st.slider("Slope window", 6, 64, 12, 1)
    z_high = st.slider("Z high threshold", 0.5, 0.95, 0.75, 0.01)
    z_stable = st.slider("Z stability (std)", 0.01, 0.2, 0.05, 0.01)

if not uploaded:
    st.stop()

df = load_csv(uploaded)
feat = compute_sled_features(df, win)
res = phase0_flags(feat, slope_win, z_high, z_stable)

st.dataframe(res.tail(20), use_container_width=True)

fig = plt.figure()
plt.plot(res["x"], label="Signal")
plt.scatter(res.index[res["Phase0"]], res.loc[res["Phase0"], "x"], label="Phase0")
plt.legend()
st.pyplot(fig)
