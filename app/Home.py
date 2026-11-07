import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))
from scrap_engine import process_scrap_stream

st.set_page_config(page_title="Circular Metals Engine", page_icon="♻️", layout="wide")

# --- PRESET LOGIC ---
PRESETS = {
    # E-Waste now has Zinc. Cu + Pb replaced by Zn to fit 1.0
    "E-Waste (PCBs)": {"Fe": 0.10, "Cu": 0.40, "Al": 0.10, "Si": 0.15, "O": 0.15, "Zn": 0.10, "C": 0.0, "P": 0.0, "S": 0.0, "Mg": 0.0},
    # Aluminum cans now have Magnesium (which vaporizes at high temps)
    "Aluminum Cans": {"Al": 0.90, "Si": 0.03, "Fe": 0.02, "O": 0.02, "Mg": 0.03, "Cu": 0.0, "C": 0.0, "P": 0.0, "S": 0.0, "Zn": 0.0},
    "End-of-Life Vehicle": {"Fe": 0.65, "Cu": 0.05, "Al": 0.15, "Si": 0.02, "O": 0.10, "C": 0.02, "P": 0.01, "S": 0.0, "Zn": 0.0, "Mg": 0.0},
    "Steel Scrap": {"Fe": 0.85, "Cu": 0.02, "Si": 0.03, "C": 0.02, "O": 0.05, "P": 0.03, "Al": 0.0, "S": 0.0, "Zn": 0.0, "Mg": 0.0}
}

def apply_preset(preset_dict):
    for k, v in preset_dict.items():
        st.session_state[f"input_{k}"] = v

with st.sidebar:
    st.header("Quick Presets")
    st.markdown("Load real-world scrap profiles:")
    for name, data in PRESETS.items():
        st.button(name, on_click=apply_preset, args=(data,), use_container_width=True)

st.title("♻️ Circular Metals Flow Engine")
st.markdown("""
Welcome to the **Physics-Informed Scrap Optimizer**. 
This tool uses a high-performance C thermodynamic kernel to predict metal recovery, calculate energy savings, and suggest valorization pathways for industrial waste.
""")

st.divider()

st.subheader("1. Define Your Scrap Stream")
st.markdown("Enter the mass percentage (0.0 to 1.0) of each element. The total must equal **1.0** (100%).")

col1, col2, col3 = st.columns(3)

with col1:
    fe = st.number_input("Iron (Fe)", min_value=0.0, max_value=1.0, value=0.60, step=0.01, key="input_Fe")
    al = st.number_input("Aluminum (Al)", min_value=0.0, max_value=1.0, value=0.20, step=0.01, key="input_Al")
    cu = st.number_input("Copper (Cu)", min_value=0.0, max_value=1.0, value=0.05, step=0.01, key="input_Cu")
    zn = st.number_input("Zinc (Zn)", min_value=0.0, max_value=1.0, value=0.00, step=0.01, key="input_Zn")
with col2:
    si = st.number_input("Silicon (Si)", min_value=0.0, max_value=1.0, value=0.05, step=0.01, key="input_Si")
    c = st.number_input("Carbon (C)", min_value=0.0, max_value=1.0, value=0.02, step=0.01, key="input_C")
    p = st.number_input("Phosphorus (P)", min_value=0.0, max_value=1.0, value=0.03, step=0.01, key="input_P")
    mg = st.number_input("Magnesium (Mg)", min_value=0.0, max_value=1.0, value=0.00, step=0.01, key="input_Mg")
with col3:
    o = st.number_input("Oxygen (O)", min_value=0.0, max_value=1.0, value=0.05, step=0.01, key="input_O")
    s = st.number_input("Sulfur (S)", min_value=0.0, max_value=1.0, value=0.00, step=0.01, key="input_S")
    
total_comp = fe + al + cu + zn + si + c + p + mg + o + s

st.divider()

st.subheader("2. Processing Parameters")
mass_kg = st.number_input("Batch Mass (kg)", min_value=100.0, value=1000.0, step=100.0, format="%.2f")
temperature = st.slider("Furnace Temperature (K)", min_value=500.0, max_value=2000.0, value=1000.0, step=50.0)

st.divider()

if st.button("Run Simulation", type="primary", use_container_width=True):
    if abs(total_comp - 1.0) > 0.01:
        st.error(f"Composition must sum to 1.0 (100%). Your current total is {total_comp:.2f}. Please adjust the inputs.")
    else:
        scrap_dict = {"Fe": fe, "Al": al, "Cu": cu, "Zn": zn, "Si": si, "C": c, "P": p, "Mg": mg, "O": o, "S": s}
        
        with st.spinner("Running C thermodynamic kernel..."):
            result = process_scrap_stream(scrap_dict, temperature=temperature, mass_kg=mass_kg)
            st.session_state['results'] = result
            st.session_state['scrap_dict'] = scrap_dict
            
        st.success("Simulation Complete! Navigate to the **Process Results** tab in the sidebar to view the analysis.")