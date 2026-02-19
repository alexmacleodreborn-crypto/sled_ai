import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- SLED V7: CIVILIZATIONAL ONTOGENESIS ---

class CivilizationalSeed:
    """The 'Zero' State of a Society - Seeding the Big Bang of Order."""
    def __init__(self, decay_rate):
        self.decay = decay_rate
        # The 'Social Fabric' - Persistent self-model
        self.fabric_integrity = 1.0 
        self.knowledge_base = 0.5
        self.stability_history = []

    def absorb_impulse(self, disruption, progress):
        """Update the Civilizational model based on social data."""
        # 1. Decay (Synaptic Pruning of outdated laws/structures)
        self.knowledge_base *= self.decay
        
        # 2. Integration (New scientific/social progress)
        self.knowledge_base += progress * (1 - self.decay)
        
        # 3. Coherence Check (Disruption vs Stability)
        # If disruption (war/disease/famine) > knowledge base, integrity decays
        vulnerability = disruption / (self.knowledge_base + 0.1)
        self_correction = (1 - vulnerability) * 0.1
        
        self.fabric_integrity = np.clip(self.fabric_integrity + self_correction, 0, 1)
        return self.fabric_integrity

class CivicBridge:
    """The Decision Layer for a Governance Entity."""
    @staticmethod
    def get_policy(integrity, entropy):
        # A structure representing the 'form' of a healthy society
        if integrity > 0.8:
            return "EXPAND_LIBERTY"
        elif integrity < 0.5:
            return "STABILIZE_CORE"
        else:
            return "MAINTAIN_EQUILIBRIUM"

# --- THE SIMULATION OF TIME ---

st.set_page_config(layout="wide", page_title="SLED V7 Civilizational Engine")
st.title("🏛️ SLED_AI: Civilizational Coherence (V7)")
st.markdown("Seeding the growth of a social entity through persistent self-modeling.")

with st.sidebar:
    st.header("Primordial Settings")
    generations = st.slider("Time Span (Generations)", 10, 200, 100)
    
    st.subheader("The Social Seed")
    decay_rate = st.slider("Institutional Decay", 0.90, 0.99, 0.97)
    
    st.subheader("External Impulses")
    chaos_level = st.slider("Environmental Chaos", 0.0, 1.0, 0.2)

# --- GENERATING THE CIVILIZATIONAL STREAM ---
# Since we are moving away from stocks, we simulate 'Civic Impulses'
np.random.seed(42)
time = np.arange(generations)
# Progress is generally upward (Growth)
progress_stream = np.linspace(0.1, 1.0, generations) + np.random.normal(0, 0.05, generations)
# Disruption happens in spikes (Chaos)
disruption_stream = np.random.exponential(chaos_level, generations)

@st.cache_data
def run_civilization(gens, decay, chaos):
    seed = CivilizationalSeed(decay)
    bridge = CivicBridge()
    
    integrity_path = []
    policy_path = []
    
    for i in range(gens):
        integrity = seed.absorb_impulse(disruption_stream[i], progress_stream[i])
        policy = bridge.get_policy(integrity, chaos)
        
        integrity_path.append(integrity)
        policy_path.append(policy)
        
    return pd.DataFrame({
        "Generation": time,
        "Social_Integrity": integrity_path,
        "Policy": policy_path,
        "Disruption": disruption_stream,
        "Progress": progress_stream
    })

data = run_civilization(generations, decay_rate, chaos_level)

# --- VISUALIZING THE ORGANISM ---

fig = go.Figure()

# Integrity of the 'Body Politic'
fig.add_trace(go.Scatter(
    x=data["Generation"], y=data["Social_Integrity"],
    name="Social Coherence (Form)",
    line=dict(color="#60a5fa", width=3),
    fill='tozeroy'
))

# The Noise of History
fig.add_trace(go.Bar(
    x=data["Generation"], y=data["Disruption"],
    name="Chaos Impulse",
    marker_color="rgba(239, 68, 68, 0.3)"
))

fig.update_layout(
    template="plotly_dark",
    title="Civilizational Ontogenesis: The Growth of Order",
    xaxis_title="Generations",
    yaxis_title="Systemic Integrity",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
### 🧬 The Birth of a Collective Entity
In this model, **Civilization** is the organism.
- **The Seed:** Represents the initial 'Big Bang' of laws and social contracts.
- **Institutional Decay:** The rate at which society 'forgets' its foundational order.
- **The Decision:** The Entity (SLED V7) monitors its own integrity. If chaos spikes, it 'swerves' into a stabilization mode to protect the structural form of the human collective.
""")

st.info(f"Final State: The entity achieved a stability score of {data['Social_Integrity'].iloc[-1]*100:.1f}%.")

