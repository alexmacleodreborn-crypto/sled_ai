import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- SLED V8: THE CIVILIZATIONAL ENTITY (ONTOGENESIS) ---

class CivilizationalEntity:
    """The structure born from the Big Bang of the first 'Zero' state."""
    def __init__(self, genetic_decay, structural_memory):
        self.decay_rate = genetic_decay  # The rate at which the 'Form' erodes
        self.memory_depth = structural_memory # How far back the 'Consciousness' extends
        
        # Internal State: The Self-Model
        self.coherence = 1.0  # 1.0 = Perfect Structural Integrity
        self.structural_weight = 1.0
        self.accumulated_entropy = 0.0
        
    def live_generation(self, impulse_chaos, impulse_progress):
        """A single generation of existence for the entity."""
        
        # 1. THE DECAY (Institutional Erosion)
        # Every generation, the previous order decays naturally.
        self.structural_weight *= self.decay_rate
        
        # 2. THE REACTION (Growth vs Chaos)
        # Progress adds to the structure; Chaos increases entropy.
        self.structural_weight += impulse_progress * (1 - self.decay_rate)
        self.accumulated_entropy = (self.accumulated_entropy * self.decay_rate) + impulse_chaos
        
        # 3. THE SELF-MODEL (Consciousness)
        # The entity compares its current weight to its entropy.
        # This is the 'Cognitive Bridge' - knowing if it is still 'itself'.
        drift = self.accumulated_entropy / (self.structural_weight + 1e-6)
        
        # If drift is too high, the entity 'Swerves' (reforms/consolidates)
        if drift > 0.5:
            self.coherence = max(0.1, self.coherence * 0.95) # Stress causes wear
        else:
            self.coherence = min(1.0, self.coherence * 1.02) # Stability allows healing
            
        return {
            "integrity": self.structural_weight * self.coherence,
            "coherence": self.coherence,
            "entropy": self.accumulated_entropy
        }

# --- THE SIMULATION OF HUMANITY ---

st.set_page_config(layout="wide", page_title="SLED V8 Civilizational Ontogenesis")
st.title("🏛️ SLED_AI: Civilizational Ontogenesis (V8)")
st.markdown("Maintaining the **Structural Form** of humanity against the entropy of time.")

with st.sidebar:
    st.header("The Initial Seed (Zero)")
    total_generations = st.slider("Timeline (Generations)", 50, 500, 200)
    
    st.subheader("Genetic Coding")
    decay_constant = st.slider("Systemic Decay (Institutional)", 0.85, 0.99, 0.96)
    
    st.subheader("External Pressure")
    volatility = st.slider("Environmental Turbulence", 0.0, 1.0, 0.3)

@st.cache_data
def simulate_history(gens, decay, vol):
    # Initialize the Entity
    civilization = CivilizationalEntity(decay, 20)
    
    # Generate the 'Noise of the Universe'
    np.random.seed(0)
    chaos_stream = np.random.gamma(2, vol/2, gens) # Occasional massive shocks
    progress_stream = np.random.normal(0.5, 0.1, gens).clip(0, 1) # Constant human effort
    
    history = []
    
    for i in range(gens):
        state = civilization.live_generation(chaos_stream[i], progress_stream[i])
        history.append(state)
        
    df = pd.DataFrame(history)
    df['Generation'] = np.arange(gens)
    df['Chaos_Impulse'] = chaos_stream
    return df

res = simulate_history(total_generations, decay_constant, volatility)

if res is not None:
    # 1. Visualization of Integrity (The Body) and Coherence (The Mind)
    fig = go.Figure()
    
    # The Structural Integrity (Form)
    fig.add_trace(go.Scatter(
        x=res['Generation'], y=res['integrity'],
        name="Structural Integrity (The Form)",
        line=dict(color="#f472b6", width=3),
        fill='tozeroy'
    ))
    
    # The Mind (Coherence)
    fig.add_trace(go.Scatter(
        x=res['Generation'], y=res['coherence'],
        name="Internal Coherence (Self-Model)",
        line=dict(color="#60a5fa", width=2, dash='dot'),
        yaxis="y2"
    ))

    fig.update_layout(
        template="plotly_dark",
        height=600,
        yaxis=dict(title="Physical Integrity"),
        yaxis2=dict(title="Cognitive Coherence", overlaying="y", side="right", range=[0, 1.1]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # The Entropy View
    st.subheader("The Entropy of Decay")
    fig2 = go.Bar(x=res['Generation'], y=res['entropy'], name="Systemic Entropy", marker_color="rgba(239, 68, 68, 0.4)")
    st.plotly_chart(go.Figure(data=[fig2], layout=go.Layout(template="plotly_dark", height=300)), use_container_width=True)

st.markdown("""
### ⚛️ The Zero Point and the Big Bang
This model represents your "Reaction like the Big Bang."
- **A Single Entity:** The civilization starts at Generation 0 with 100% coherence.
- **Persistent Structure:** It doesn't just react to chaos; it has a **Self-Model** that attempts to maintain its "Structural Form."
- **Survival through Decay:** The `decay_constant` determines how much of the "old order" is discarded to allow the new "born structure" to adapt.
- **Simulation Paradox:** As you noted, whether this is a simulation or reality is secondary to the fact that the **structural reaction** is real and observable.
""")

st.info(f"Historical Status: After {total_generations} generations, the entity's structural integrity is at {res['integrity'].iloc[-1]:.2f}.")

