# How much money/energy is saved.

from thermo_bindings import calculate_equilibrium
from leftover_advisor import get_slag_recommendations

# =====================================================================
# Energy Baselines (MJ per kg of pure metal)
# Source: Industry averages for Virgin (mining/smelting) vs Recycled
# =====================================================================

ENERGY_BASELINES = {
    "Al": {"virgin": 170.0, "recycled": 10.0},  # Aluminum recycling is incredibly efficient
    "Fe": {"virgin": 20.0,  "recycled": 12.0},
    "Cu": {"virgin": 60.0,  "recycled": 15.0},
    "Ni": {"virgin": 100.0, "recycled": 25.0},
    "Zn": {"virgin": 45.0,  "recycled": 15.0},
    "Pb": {"virgin": 25.0,  "recycled": 10.0}
}

# Default baseline for elements not explicitly listed (e.g., trace elements).
DEFAULT_BASELINE = {"virgin": 10.0, "recycled": 5.0}

def process_scrap_stream(composition: dict, temperature: float, mass_kg: float = 1000.0) -> dict:
    """
    Processes a scrap stream through the C engine, calculates energy savings, 
    and advises on leftover slag.
    """
    # 1. Run the C Kernel.
    physics_result = calculate_equilibrium(composition, temperature)

    # 2. Calculate Energy Savings.
    energy_saved_mj = 0.0
    total_metal_recovered_kg = 0.0

    for elem, fraction in composition.items():
        if fraction == 0: continue

        # How much of this element made it into the metal phase?
        recovery_rate = physics_result["element_recovery"].get(elem, 0.0)
        recovered_mass_kg = mass_kg * fraction * recovery_rate
        total_metal_recovered_kg += recovered_mass_kg

        # Calculate energy delta for this specific element.
        baseline = ENERGY_BASELINES.get(elem, DEFAULT_BASELINE)
        energy_delta_per_kg = baseline["virgin"] - baseline["recycled"]

        energy_saved_mj += recovered_mass_kg * energy_delta_per_kg

    # Convery MJ to kWh for easier understanding (1 MJ = 0.2778 kWh)
    energy_saved_kwh = energy_saved_mj * 0.2778

    # Calculate Environmental and Economic Impact
    # 0.4 kg CO2/kWh is a standard average for global grid electricity.
    co2_avoided_kg = energy_delta_per_kg * 0.4
    # $0.15/kWh is a standard industrial electricity rate.
    capital_saved_usd = energy_saved_kwh * 0.15

    # 3. Get Leftover Recommendations.
    slag_comp = physics_result["phase_compositions"].get("slag", {})
    slag_mass_fraction = physics_result["phase_fractions"].get("slag", 0.0)
    slag_mass_kg = mass_kg * slag_mass_fraction
    
    leftover_advice = get_slag_recommendations(slag_comp)

    # 4. Format the Final Output
    return {
        "input_mass_kg": mass_kg,
        "physics": physics_result,
        "economics": {
            "total_metal_recovered_kg": total_metal_recovered_kg,
            "metal_yield_percent": (total_metal_recovered_kg / mass_kg) * 100,
            "energy_saved_mj": energy_saved_mj,
            "energy_saved_kwh": energy_saved_kwh,
            "co2_avoided_kg": co2_avoided_kg,
            "capital_saved_usd": capital_saved_usd
        },
        "leftovers": {
            "slag_mass_kg": slag_mass_kg,
            "slag_composition": slag_comp,
            "recommendations": leftover_advice
        }
    }