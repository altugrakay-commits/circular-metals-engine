import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")

st.title("📊 Simulation Results")

# Check if results exist
if 'results' not in st.session_state:
    st.warning("No simulation data found. Please go to the **Home** page and run a simulation first.")
    st.stop()

res = st.session_state['results']
scrap_dict = st.session_state['scrap_dict']

# --- TOP METRICS ---
st.subheader("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Metal Yield", f"{res['economics']['metal_yield_percent']:.1f} %")
col2.metric("Energy Saved", f"{res['economics']['energy_saved_kwh']:,.0f} kWh")
col3.metric("CO₂ Avoided", f"{res['economics']['co2_avoided_kg']:,.0f} kg")
col4.metric("Capital Saved", f"${res['economics']['capital_saved_usd']:,.2f}")

st.divider()

# --- CHARTS ---
colA, colB = st.columns(2)

with colA:
    st.markdown("### Mass Balance (Phase Distribution)")
    # Filter out phases with 0 mass
    phase_data = {k: v for k, v in res['physics']['phase_fractions'].items() if v > 0.001}
    
    fig = go.Figure(data=[go.Pie(
        labels=list(phase_data.keys()), 
        values=list(phase_data.values()), 
        hole=.4,
        marker_colors=['#00CC96', '#EF553B', '#636EFA']
    )])
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with colB:
    st.markdown("### Recovered Metal Composition")
    metal_comp = res['physics']['phase_compositions'].get('metal', {})
    
    # Sort for nice bar chart
    sorted_metal = dict(sorted(metal_comp.items(), key=lambda item: item[1]))
    
    fig2 = go.Figure(data=[go.Bar(
        x=list(sorted_metal.values()),
        y=list(sorted_metal.keys()),
        orientation='h',
        marker_color='#00CC96'
    )])
    fig2.update_layout(xaxis_title="Fraction within Metal Phase", yaxis_title="Element", margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- LEFTOVER ADVISOR ---
st.subheader("♻️ Leftover Valorization Advisor")
st.markdown("Our physics model evaluated the chemical composition of the slag phase to suggest industrial symbiosis pathways.")

if res['leftovers']['slag_mass_kg'] > 0.1:
    for rec in res['leftovers']['recommendations']:
        st.info(f"**Recommended Use:** {rec['use']} (Confidence: {rec['confidence']*100:.0f}%)\n\n*Reasoning:* {rec['reason']}")
    
    with st.expander("View Raw Slag Composition"):
        st.write(res['leftovers']['slag_composition'])
else:
    st.success("No slag generated in this simulation. 100% of the material reported to the metal or gas phase!")