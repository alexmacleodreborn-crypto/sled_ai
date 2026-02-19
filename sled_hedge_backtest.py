import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SLED V5: PRIMORDIAL ZERO ARCHITECTURE ---

class PrimordialSeed:
    """The 'Zero' State - A single reaction seeding a structural form."""
    def __init__(self, initial_decay):
        self.decay_rate = initial_decay
        self.memory = 0.5 # The 'form' starts at neutral potential
        self.structural_integrity = 1.0

    def react(self, impulse):
        """A single impulse creates a decay-based structural update."""
        # This is the 'Big Bang' logic: Reaction leads to expansion or contraction
        self.memory = (self.memory * self.decay_rate) + (impulse * (1 - self.decay_rate))
        return self.memory

class WorldPatternLayer:
    """Layer 1: Observing the Environment's Vibration"""
    @staticmethod
    def extract_vibration(df, seed):
        df = df.copy()
        df['impulse'] = df['Close'].pct_change().fillna(0)
        
        # The Seed processes the environment
        vibration_history = []
        for val in df['impulse']:
            vibration_history.append(seed.react(val))
            
        df['vibration'] = vibration_history
        # Entropy is now the 'Decay of Certainty'
        df['entropy'] = df['vibration'].rolling(10).std().fillna(0)
        return df

class EmbodimentLayer:
    """Layer 2: The Organism's Need to Maintain Form"""
    def __init__(self, decay_limit):
        self.decay_limit = decay_limit
        self.peak = 1.0

    def evaluate_form(self, current_nav, peak_nav):
        # Integrity is the distance from 'Zero' (Death/Drawdown)
        integrity = current_nav / peak_nav
        return integrity

class LogicalBridge:
    """Layer 3: Purposeful Agency - The Born Structure"""
    def __init__(self, threshold):
        self.threshold = threshold
        self.state = "DORMANT" # Starts as a potential, not an action

    def synthesize(self, vibration, integrity, entropy):
        # The bridge creates 'Intent' based on the Organism's growth
        # If vibration exceeds the threshold of the 'Seed', it 'Swerves'
        if abs(vibration) > self.threshold or integrity < 0.88:
            self.state = "PROTECTING"
            return 1.0 # 100% Defensive
        
        # If entropy (uncertainty) decays, the form re-expands
        if entropy < (self.threshold * 0.5):
            self.state = "EXPANDING"
            return 0.0
            
        return 1.0 if self.state == "PROTECTING" else 0.0

# --- THE EVOLUTIONARY SIMULATION ---

st.set_page_config(layout="wide", page_title="SLED V5 Primordial Zero")
st.title("🧬 SLED_AI: Primordial Zero (V5)")
st.markdown("A structure born from the decay of initial potentiality.")

with st.sidebar:
    st.header("Seeding Parameters")
    ticker = st.text_input("Environmental Ticker", "SPY")
    
    st.subheader("The Seed")
    decay_val = st.slider("Decay Rate (Memory)", 0.80, 0.99, 0.95)
    reaction_thresh = st.slider("Reaction Threshold", 0.001, 0.02, 0.005, format="%.3f")
    
    st.subheader("The Form")
    survival_need = st.slider("Integrity Floor", 0.80, 0.95, 0.88)

@st.cache_data
def evolve_entity(symbol, decay, thresh, floor):
    try:
        df = yf.download(symbol, start="2010-01-01", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Initialize Entity
        seed = PrimordialSeed(decay)
        body = EmbodimentLayer(floor)
        bridge = LogicalBridge(thresh)
        
        df = WorldPatternLayer.extract_vibration(df, seed)
        
        cash, shares, peak = 100000, 0, 100000
        shares = cash / df['Close'].iloc[0]
        cash = 0
        
        history = []
        
        for i in range(len(df)):
            p = df['Close'].iloc[i]
            nav = cash + (shares * p)
            peak = max(peak, nav)
            
            integrity = body.evaluate_form(nav, peak)
            
            # The Entity Synthesizes its state
            hedge_intent = bridge.synthesize(
                df['vibration'].iloc[i], 
                integrity, 
                df['entropy'].iloc[i]
            )
            
            # Physical Rebalancing (Action follows Form)
            target_cash = nav * hedge_intent
            if cash < target_cash:
                to_sell = (target_cash - cash) / p
                qty = min(shares, to_sell)
                shares -= qty
                cash += qty * p
            elif hedge_intent == 0.0 and cash > 0:
                shares += cash / p
                cash = 0
                
            history.append(cash + shares * p)
            
        df['equity'] = history
        df['bh'] = (df['Close'] / df['Close'].iloc[0]) * 100000
        df['dd'] = (df['equity'].cummax() - df['equity']) / df['equity'].cummax()
        return df
    except Exception as e:
        st.error(f"Seeding Failed: {e}")
        return None

res = evolve_entity(ticker, decay_val, reaction_thresh, survival_need)

if res is not None:
    c1, c2, c3 = st.columns(3)
    yrs = (res.index[-1] - res.index[0]).days / 365.25
    c1.metric("Structural CAGR", f"{((res['equity'].iloc[-1]/100000)**(1/yrs)-1)*100:.2f}%")
    c2.metric("Form Integrity (Max DD)", f"{res['dd'].max()*100:.2f}%")
    c3.metric("Final Form Capital", f"${res['equity'].iloc[-1]:,.0f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res.index, y=res['bh'], name="Environment (B&H)", line=dict(color="rgba(255,255,255,0.2)", dash="dot")))
    fig.add_trace(go.Scatter(x=res.index, y=res['equity'], name="Entity: SLED V5", line=dict(color="#8b5cf6", width=2)))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,b=0,t=20))
    st.plotly_chart(fig, use_container_width=True)

