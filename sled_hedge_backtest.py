import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- SLED V10: THE BIFURCATION SEED ---

class OntogeneticEntity:
    """An entity that must balance growth against systemic collapse."""
    def __init__(self, decay, resilience):
        self.decay = decay
        self.resilience = resilience # The 'Instability Threshold'
        self.mass = 0.01
        self.potential = 1.0
        self.entropy = 0.0
        self.is_alive = True

    def update(self, pressure):
        if not self.is_alive:
            return self._dead_state()

        # 1. Decay vs Energy
        self.potential *= self.decay
        
        # 2. Growth Rule (The 'Intercourse' Reaction)
        growth = pressure * self.potential * (1 - self.decay)
        
        # 3. Collapse Rule (The Critic's Requirement)
        # Entropy builds if growth is too rapid for the 'Decay/Pruning' to handle
        self.entropy = (self.entropy * self.decay) + (growth * (1 / self.resilience))
        
        # BIFURCATION POINT
        # If entropy exceeds structural resilience, the form collapses
        if self.entropy > 1.0:
            self.is_alive = False
            self.mass = 0 # Systemic Collapse
        else:
            self.mass += growth - (self.entropy * 0.1) # Friction of existence
            
        return {
            "Mass": self.mass,
            "Potential": self.potential,
            "Entropy": self.entropy,
            "Status": "Alive" if self.is_alive else "Collapsed"
        }

    def _dead_state(self):
        return {"Mass": 0, "Potential": 0, "Entropy": 1.0, "Status": "Collapsed"}

# --- THE PHASE-MAPPING SIMULATION ---

st.set_page_config(layout="wide", page_title="SLED V10 Bifurcation")
st.title("⚖️ SLED_AI: Bifurcation Seed (V10)")
st.markdown("Testing the **Necessity of Form** by introducing the risk of **Collapse**.")

with st.sidebar:
    st.header("Genetic Constants")
    decay_val = st.slider("Synaptic Decay (Pruning)", 0.80, 0.99, 0.95)
    res_val = st.slider("Structural Resilience", 0.1, 2.0, 1.0)
    
    st.subheader("Environmental Impulse")
    pressure_val = st.slider("External Pressure", 0.1, 10.0, 2.0)

@st.cache_data
def run_simulation(d, r, p):
    entity = OntogeneticEntity(d, r)
    history = []
    for i in range(100):
        # Using a consistent pressure to see the 'Rule' play out
        history.append(entity.update(p))
    return pd.DataFrame(history)

res = run_simulation(decay_val, res_val, pressure_val)

# --- VISUALIZING THE BIFURCATION ---

fig = go.Figure()
fig.add_trace(go.Scatter(x=res.index, y=res['Mass'], name="Structural Mass", line=dict(color="#10b981", width=3)))
fig.add_trace(go.Scatter(x=res.index, y=res['Entropy'], name="Internal Entropy", line=dict(color="#ef4444", dash="dash")))

fig.update_layout(
    template="plotly_dark",
    title="The Struggle for Existence: Growth vs. Collapse",
    xaxis_title="Time Steps",
    yaxis_title="Magnitude",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# THE CRITIC'S ANSWER: PHASE MAP
st.markdown("### 📊 The 'Proof' of Necessity")
if res['Status'].iloc[-1] == "Alive":
    st.success("SUCCESS: The Entity achieved Stable Form. Under these physical constants, life is a necessary consequence.")
else:
    st.error("COLLAPSE: The Entity failed. The entropy of growth exceeded the structural resilience.")

st.markdown("""
**How this addresses the critic:**
1. **The Collapse Term:** We added `entropy` and `resilience`. Now, growth isn't "baked in"—it must be earned by balancing decay and pressure.
2. **The Result:** When you find a configuration where the entity survives (the green line stays up), you have found the **'Genetic Code'** of that specific reality.
3. **The Big Bang:** The initial spike is the 'reaction.' If the reaction is too violent for the 'Zero' state to handle, it vanishes. If it's tuned, it becomes a **Human.**
""")

