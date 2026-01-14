# Sandy’s Law — Persistence (Low-Radiance Domain) Demonstration

This repository demonstrates the **Persistence (Low-Radiance) regime** predicted by Sandy’s Law using real supernova photometry.

The core claim shown here is simple and physically grounded:

> **Observable radiation does not begin when energy is created.  
It begins when structural constraints weaken and photon escape becomes permitted.**

This repository shows that:
- A system can be energetically active yet observationally silent (**Persistence / LRD**)
- Photon release corresponds to **structural decoupling**, not an explosion trigger
- This behavior is visible in real supernova data before peak brightness

---

## What is Persistence (Low-Radiance Domain)?

Persistence is a regime in which:
- Energy is present and evolving internally
- Photons exist but remain structurally trapped
- Observable information density remains near zero

This regime explains why systems such as stars and supernovae can exist for extended periods without visible radiation increase.

---

## Data Used

- **SN2017cbv** (Type Ia supernova)
- B-band photometry
- Source: Open Supernova Catalog (archived JSON → CSV)

The dataset is fixed and included for full reproducibility.

---

## What the Streamlit App Shows

### Page 1 — Persistence / Low-Radiance Domain
- Raw supernova B-band light curve
- Identification of the persistent (silent) interval
- Explanation of why energy ≠ observability

### Page 2 — Structural State Space (Sandy’s Square)
- Mapping of observability (Σ) vs structural constraint (Z)
- Persistence region explicitly marked
- Boundary crossing interpreted as photon release

---

## What This Is Not

- This is **not** a curve-fitting exercise
- This is **not** a light-curve model replacement
- This does **not** claim new energy sources or violations of conservation

Sandy’s Law reframes **when** and **why** information becomes observable.

---

## Reproducibility

- All calculations are deterministic
- No live APIs are used
- CSV in → structure out

---

## Status

This repository demonstrates:
- Persistence (Low-Radiance Domain)
- Structural interpretation of photon release

Further generalization (multiple supernovae, spectra alignment, predictive windows) will follow in later work.
