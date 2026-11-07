# python/test_engine.py
import json
from scrap_engine import process_scrap_stream

def test_full_engine():
    print("Testing Scrap Engine & Leftover Advisor...\n")
    
    # 1. A 1-ton batch of mixed Aluminum scrap
    scrap_mix = {
        "Al": 0.70,  # 700 kg of Aluminum (very high energy savings)
        "Fe": 0.15,  # 150 kg of Iron (tramp metal)
        "Si": 0.05,  # 50 kg of Silicon
        "O":  0.10   # 100 kg of Oxygen (forms slag)
    }
    
    # 2. Process it
    result = process_scrap_stream(scrap_mix, temperature=1000.0, mass_kg=1000.0)
    
    # 3. Print the results beautifully
    print("--- ECONOMICS ---")
    print(f"Total Metal Recovered: {result['economics']['total_metal_recovered_kg']:.1f} kg")
    print(f"Metal Yield:           {result['economics']['metal_yield_percent']:.1f}%")
    print(f"Energy Saved:          {result['economics']['energy_saved_kwh']:.1f} kWh")
    
    print("\n--- LEFTOVER ADVISOR (Slag) ---")
    print(f"Slag Mass:             {result['leftovers']['slag_mass_kg']:.1f} kg")
    for rec in result['leftovers']['recommendations']:
        print(f"-> {rec['use']} (Confidence: {rec['confidence']*100:.0f}%)")
        print(f"   Reason: {rec['reason']}")

if __name__ == "__main__":
    test_full_engine()