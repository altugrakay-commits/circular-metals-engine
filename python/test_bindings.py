from thermo_bindings import calculate_equilibrium

def test_python_bindings():
    print("Testing Python -> C Bindings...")
    
    # The exact same mixed scrap composition we tested in C
    scrap_mix = {
        "Fe": 0.90,
        "Cu": 0.02,
        "C": 0.01,
        "O": 0.04,
        "S": 0.01,
        "P": 0.02
    }
    
    # Run it
    res = calculate_equilibrium(scrap_mix, temperature=1873.0, pressure=1.0)
    
    print("\n--- Phase Fractions (Mass Balance) ---")
    for phase, frac in res["phase_fractions"].items():
        print(f"{phase.capitalize()}: {frac:.4f}")
        
    print("\n--- Metal Phase Composition ---")
    for elem, frac in res["phase_compositions"]["metal"].items():
        print(f"{elem}: {frac:.4f}")
        
    print("\n--- Assertions ---")
    assert abs(res["phase_fractions"]["metal"] - 0.92) < 1e-6, "Metal fraction failed"
    assert abs(res["phase_fractions"]["slag"] - 0.06) < 1e-6, "Slag fraction failed"
    assert abs(res["phase_fractions"]["gas"] - 0.02) < 1e-6, "Gas fraction failed"
    
    total = sum(res["phase_fractions"].values())
    assert abs(total - 1.0) < 1e-6, "Total mass balance failed"
    
    assert abs(res["phase_compositions"]["metal"]["Fe"] - (0.90/0.92)) < 1e-6, "Fe fraction failed"
    
    print("\n✅ ALL PYTHON BINDING TESTS PASSED!")

if __name__ == "__main__":
    test_python_bindings()