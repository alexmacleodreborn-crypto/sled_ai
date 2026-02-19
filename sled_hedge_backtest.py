import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- SLED V11: A7DO GESTATION & VILLAGE LEARNING ---

class A7DO_Entity:
    """The central entity gestating from a Zero-Point seed."""
    def __init__(self, decay, resilience):
        self.decay = decay
        self.resilience = resilience
        self.age = 0
        self.mass = 0.05
        self.potential = 1.0
        self.coherence = 1.0
        self.is_born = False
        self.position = np.array([0.5, 0.5]) # Center of the village
        self.experience_map = []

    def gestate(self, maternal_impulse):
        """Internal growth before entering the 'Village'."""
        self.potential *= self.decay
        growth = maternal_impulse * self.potential * (1 - self.decay)
        self.mass += growth
        self.age += 1
        
        if self.mass > 0.5: # Threshold for 'Birth'
            self.is_born = True
        return self.is_born

    def learn_from_village(self, neighbors):
        """Post-birth interaction with the neighborhood."""
        # Neighbors provide 'Impulses' based on proximity
        social_pressure = 0
        for n_pos in neighbors:
            dist = np.linalg.norm(self.position - n_pos)
            # Inverse square law of social influence
            social_pressure += 1 / (dist**2 + 0.1)
        
        # Structure adapts to social pressure
        self.potential *= self.decay
        adaptation = (social_pressure * 0.001) * self.potential
        self.mass += adaptation
        
        # Random walk / Exploration of the village
        self.position += np.random.normal(0, 0.02, 2)
        self.position = np.clip(self.position, 0, 1)
        
        self.experience_map.append(self.position.copy())
        return self.mass

# --- THE VILLAGE ENVIRONMENT ---

st.set_page_config(layout="wide", page_title="SLED V11 Village")
st.title("🏘️ SLED_AI: A7DO Village Gestation (V11)")
st.markdown("From the **Seed** to the **Village**: Modeling the birth and social learning of a structural entity.")

with st.sidebar:
    st.header("1. Gestation (The Seed)")
    maternal_strength = st.slider("Maternal Impulse (Initial)", 1.0, 10.0, 5.0)
    biological_decay = st.slider("Biological Pruning", 0.90, 0.99, 0.96)
    
    st.header("2. The Village (Context)")
    num_neighbors = st.slider("Village Density", 5, 50, 15)
    social_chaos = st.slider("Social Turbulence", 0.0, 1.0, 0.2)

# --- THE PROCESS ---

@st.cache_data
def run_gestation_and_life(m_imp, decay, n_count, chaos):
    # Initialize A7DO
    child = A7DO_Entity(decay, 1.0)
    
    # 1. GESTATION PHASE
    gestation_history = []
    while not child.is_born and child.age < 50:
        is_born = child.gestate(m_imp + np.random.normal(0, chaos))
        gestation_history.append({"Age": child.age, "Mass": child.mass, "Stage": "Gestation"})
    
    # 2. VILLAGE PHASE (Post-Birth)
    village_neighbors = np.random.rand(n_count, 2)
    life_history = []
    for _ in range(100):
        mass = child.learn_from_village(village_neighbors)
        life_history.append({
            "Age": child.age + _, 
            "Mass": mass, 
            "X": child.position[0], 
            "Y": child.position[1],
            "Stage": "Social Learning"
        })
        
    return pd.DataFrame(gestation_history), pd.DataFrame(life_history), village_neighbors

gest_df, life_df, neighbors = run_gestation_and_life(maternal_strength, biological_decay, num_neighbors, social_chaos)

# --- VISUALIZING THE BIRTH ---

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("The Growth Curve (Gestation to Life)")
    combined_growth = pd.concat([gest_df, life_df])
    fig_growth = px.line(combined_growth, x="Age", y="Mass", color="Stage", title="Structural Accumulation")
    fig_growth.update_layout(template="plotly_dark")
    st.plotly_chart(fig_growth, use_container_width=True)

with col2:
    st.subheader("The Village Canvas (Spatial Learning)")
    # Plot Neighbors
    fig_village = go.Figure()
    fig_village.add_trace(go.Scatter(
        x=neighbors[:, 0], y=neighbors[:, 1],
        mode='markers', name='Village Agents',
        marker=dict(size=10, color='rgba(255,255,255,0.3)')
    ))
    # Plot A7DO's Path
    fig_village.add_trace(go.Scatter(
        x=life_df['X'], y=life_df['Y'],
        mode='lines+markers', name='A7DO Learning Path',
        line=dict(color='#facc15', width=2),
        marker=dict(size=5, color='#8b5cf6')
    ))
    fig_village.update_layout(template="plotly_dark", xaxis=dict(range=[0,1]), yaxis=dict(range=[0,1]))
    st.plotly_chart(fig_village, use_container_width=True)

st.markdown(f"""
### 🧬 A7DO is Born
The system has simulated the movement from **Zero** to **Village**.
- **Gestation:** The entity grows in the 'dark' (the sidebar settings) until its mass exceeds the threshold of birth.
- **The Village:** Once born, A7DO moves through the neighborhood. Its growth is now a function of its **distance to others**.
- **The Result:** The path in the right-hand chart is the 'Experience Map'. It shows how the structure navigates social impulses.
""")

st.info(f"Life Summary: A7DO was born at Age {gest_df['Age'].max()} and has traveled through {num_neighbors} social impulses.")

