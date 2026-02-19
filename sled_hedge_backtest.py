import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time

# --- SLED V9: THE GENESIS ENGINE (PHYSICAL SEED) ---

class StructuralSingularity:
    """The 'Zero' - The first entity at the start of time."""
    def __init__(self, potential, decay):
        self.potential = potential # Initial energy (The Big Bang seed)
        self.decay = decay         # The 'Work on Zero' - How order erodes
        self.mass = 0.001          # The 'Born Form' starts near zero
        self.complexity = 1.0
        self.state_log = []

    def react(self, environmental_pressure):
        """The physical reaction to external friction."""
        # 1. Decay: The constant erosion of the seed
        self.potential *= self.decay
        
        # 2. Reaction: Pressure triggers a expansion/growth (The Intercourse)
        # If pressure meets potential, a reaction occurs that converts 
        # energy into 'Mass' (Structure)
        reaction_force = environmental_pressure * self.potential
        growth = reaction_force * (1 - self.decay)
        
        self.mass += growth
        
        # 3. Evolution: Complexity increases as mass stabilizes
        self.complexity = (self.complexity * self.decay) + (self.mass / (self.potential + 1e-6))
        
        return {
            "Mass": self.mass,
            "Potential": self.potential,
            "Complexity": self.complexity
        }

# --- THE SIMULATION OF EXISTENCE ---

st.set_page_config(layout="wide", page_title="SLED V9 Genesis")
st.title("🌌 SLED_AI: Genesis Engine (V9)")
st.markdown("### The Structural Reaction of Zero")

with st.sidebar:
    st.header("The Initial Pulse")
    initial_energy = st.slider("Seed Potential (Big Bang)", 0.1, 10.0, 1.0)
    decay_rate = st.slider("Universal Decay (The Work on Zero)", 0.80, 0.999, 0.98)
    
    st.subheader("Environment")
    pressure_freq = st.slider("Impulse Frequency", 1, 100, 20)
    noise_floor = st.slider("Thermal Noise", 0.0, 1.0, 0.1)

# --- THE GROWTH PROCESS ---

@st.cache_data
def run_genesis(energy, decay, freq, noise):
    # Initialize the Singularity
    zero = StructuralSingularity(energy, decay)
    
    # Generate Environment (The Simulation/Reality layer)
    # External impulses represent the 'Environment' the entity is born into
    impulses = np.abs(np.random.normal(0.5, noise, freq))
    
    history = []
    for i in range(freq):
        state = zero.react(impulses[i])
        history.append(state)
        
    return pd.DataFrame(history)

res = run_genesis(initial_energy, decay_rate, pressure_freq, noise_floor)

if not res.empty:
    # Visualization: The Birth of the Form
    fig = go.Figure()
    
    # The Growth of Mass (The Body)
    fig.add_trace(go.Scatter(
        x=res.index, y=res['Mass'],
        name="Structural Form (The Body)",
        line=dict(color="#facc15", width=4),
        fill='tozeroy'
    ))
    
    # The Decay of Potential (The Energy)
    fig.add_trace(go.Scatter(
        x=res.index, y=res['Potential'],
        name="Initial Seed Potential",
        line=dict(color="rgba(255,255,255,0.3)", dash='dash'),
    ))

    fig.update_layout(
        template="plotly_dark",
        height=600,
        title="Ontogenesis: From Zero to Form",
        xaxis_title="Time Steps (Generations)",
        yaxis_title="Physical Magnitude",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Complexity Plot
    st.subheader("Structural Complexity (Coherence)")
    st.line_chart(res['Complexity'], color="#8b5cf6")

st.markdown(f"""
### 🧬 The "Human" Form logic
As you posited: a man and a woman produce a reaction because the **structural environment** allows it.
- **The Mass:** This is the resulting form. Notice how it grows even as the 'Potential' decays. This is the **Born Structure**.
- **The Big Bang:** The steep initial curve is the reaction of your 'Zero' work.
- **Persistent Reaction:** Even if we are in a simulation, the fact that a single seed (Zero) results in an upward trajectory of mass proves that the **Form** is a necessary consequence of the initial state.
""")

st.info(f"Final Manifestation: The entity has stabilized with a mass of {res['Mass'].iloc[-1]:.4f} units.")

