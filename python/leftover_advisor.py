# Tells what to do with the waste.

def get_slag_recommendations(slag_composition: dict) -> list[dict]:
    """
    Takes the slag composition (fractions within the slag phase) 
    and returns suggested valorization pathways.
    """
    # Helper function to safely get element fractions.
    def get(elem): return slag_composition.get(elem, 0.0)

    recommendations = []

    # Rule 1: High Calcium + Silicon -> Cement / Construction
    # Typical steelmaking slag is rich in CaO and SiO2
    if get("O") > 0.30 and get("Si") > 0.10:
        recommendations.append({
            "use": "Supplementary Cementitious Material (SCM)",
            "confidence": 0.85,
            "reason": "High oxygen and silicon content. The slag acts as a pozzolan, "
            "reducing the need for Portland cement and lowering CO2 emissions."
        })

    # Rule 2: High Iron/Oxygen -> Iron reovery or Road base
    if get("Fe") > 0.15:
        recommendations.append({
            "use": "Construction Aggregate / Road Base",
            "confidence": 0.75,
            "reason": "High residual iron oxide content. This makes the slag dense and durable, "
            "ideal for road foundation, or can be sent for secondary iron recovery."
        })

    # Rule 3: High Phosphorus -> Fertilizer
    if get("P") > 0.05:
        recommendations.append({
            "use": "Agricultural Fertilizer (Fertilizer Slag)",
            "confidence": 0.80,
            "reason": "Elevated phosphorus. Basic oxygen furnace (BOF) slag with P "
            "can be processed into slow-release phosphate fertilizer"
        })

    # Rule 4: Aluminum-rich -> Refractory or Alumina recovery
    if get("Al") > 0.20:
        recommendations.append({
            "use": "Alumina Recovery / Refractory Material",
            "confidence": 0.70,
            "reason": "High aluminum content. Can be processed to recover alumina "
            "or used as a refractory lining material."
        })

    # Fallback if no specific rules are triggered.
    if not recommendations:
        recommendations.append({
            "use": "Landfill / Monofill (requires further processing)",
            "confidence": 0.50,
            "reason": "Composition lacks the specific oxides required for industrial symbiosis. "
            "Consider adding fluxes to improve future recyclability."
        })

    return recommendations