import ctypes
import os
import platform

# =====================================================================
# 1. Define the exact C-struct mirrors
# =====================================================================
N_ELEMENTS = 15
N_PHASES = 3

ELEMENTS = ["Fe", "Cu", "Al", "Zn", "Pb", "Ni", "Cr", "Mn", "Si", "C", "O", "S", "P", "Sn", "Mg"]
PHASES = ["metal", "slag", "gas"]

class ThermoInput(ctypes.Structure):
    _fields_ = [
        ("composition", ctypes.c_double * N_ELEMENTS),
        ("temperature", ctypes.c_double),
        ("pressure", ctypes.c_double),
        ("flux_cao_kg_per_t", ctypes.c_double),
        ("flux_mgo_kg_per_t", ctypes.c_double),
        ("max_iterations", ctypes.c_int)
    ]

class ThermoOutput(ctypes.Structure):
    _fields_ = [
        ("phase_fractions", ctypes.c_double * N_PHASES),
        ("phase_compositions", (ctypes.c_double * N_ELEMENTS) * N_PHASES),
        ("element_recovery", ctypes.c_double * N_ELEMENTS),
        ("energy_delta_kj_per_kg", ctypes.c_double),
        ("gibbs_free_energy_kj_per_mol", ctypes.c_double),
        ("iterations_used", ctypes.c_int),
        ("status", ctypes.c_int)
    ]

# =====================================================================
# 2. Attempt to load the C shared library
# =====================================================================
_lib = None
USE_C_KERNEL = False

def _load_library():
    global _lib, USE_C_KERNEL
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if platform.system() == "Windows":
        lib_name = "libthermo.dll"
    elif platform.system() == "Darwin":
        lib_name = "libthermo.dylib"
    else:
        lib_name = "libthermo.so"
        
    lib_path = os.path.join(current_dir, "..", "c_kernel", lib_name)
    
    if not os.path.exists(lib_path):
        print(f"⚠️ C library not found at {lib_path}. Using Pure Python Fallback.")
        return
        
    try:
        _lib = ctypes.CDLL(lib_path)
        _lib.thermo_calculate_equilibrium.argtypes = [ctypes.POINTER(ThermoInput), ctypes.POINTER(ThermoOutput)]
        _lib.thermo_calculate_equilibrium.restype = ctypes.c_int
        USE_C_KERNEL = True
        print("✅ Successfully loaded C Thermodynamic Kernel.")
    except Exception as e:
        print(f"⚠️ Failed to load C library: {e}. Using Pure Python Fallback.")

_load_library()

# =====================================================================
# 3. Pure Python Fallback (For Streamlit Cloud)
# =====================================================================
def _calculate_equilibrium_python(composition_dict: dict, temperature: float) -> dict:
    # Base partition matrix
    part = {
        "metal": {"Fe": 1, "Cu": 1, "Al": 1, "Zn": 1, "Pb": 1, "Ni": 1, "Cr": 1, "Mn": 1, "Sn": 1, "Mg": 1},
        "slag":  {"O": 1, "P": 1, "Si": 1},
        "gas":   {"C": 1, "S": 1}
    }
    
    # Get all elements
    elems = ELEMENTS
    
    # Dynamic temperature shift for volatile elements
    temp_factor = max(0.0, min(1.0, (temperature - 1000.0) / 1000.0))
    for volatile in ["Zn", "Pb", "Mg"]:
        shift = part["metal"].get(volatile, 0.0) * 0.5 * temp_factor
        if shift > 0:
            part["metal"][volatile] = part["metal"].get(volatile, 0.0) - shift
            part["gas"][volatile] = part["gas"].get(volatile, 0.0) + shift
            
    # Initialize outputs
    phase_fracs = {p: 0.0 for p in PHASES}
    phase_comps = {p: {e: 0.0 for e in elems} for p in PHASES}
    recovery = {e: 0.0 for e in elems}
    
    # Calculate phase masses
    for p in PHASES:
        for e in elems:
            c = composition_dict.get(e, 0.0)
            frac = part[p].get(e, 0.0)
            phase_fracs[p] += c * frac
            
    # Calculate intra-phase compositions and recovery
    for p in PHASES:
        denom = phase_fracs[p]
        if denom > 1e-12:
            for e in elems:
                c = composition_dict.get(e, 0.0)
                frac = part[p].get(e, 0.0)
                phase_comps[p][e] = (c * frac) / denom
                
    for e in elems:
        recovery[e] = part["metal"].get(e, 0.0)
        
    return {
        "phase_fractions": phase_fracs,
        "phase_compositions": phase_comps,
        "element_recovery": recovery,
        "energy_delta_kj_per_kg": (temperature - 298.15) * 0.05,
        "gibbs_free_energy": 0.0,
        "iterations_used": 1,
        "status": "OK"
    }

# =====================================================================
# 4. The Unified Wrapper
# =====================================================================
def calculate_equilibrium(composition_dict: dict, temperature: float, pressure: float = 1.0) -> dict:
    if not USE_C_KERNEL:
        return _calculate_equilibrium_python(composition_dict, temperature)

    # --- C Kernel Path ---
    in_struct = ThermoInput()
    out_struct = ThermoOutput()
    
    total_composition = 0.0
    for idx, elem in enumerate(ELEMENTS):
        val = composition_dict.get(elem, 0.0)
        in_struct.composition[idx] = val
        total_composition += val
        
    if abs(total_composition - 1.0) > 1e-3:
        raise ValueError(f"Composition must sum to 1.0, got {total_composition:.4f}")
        
    in_struct.temperature = temperature
    in_struct.pressure = pressure
    in_struct.flux_cao_kg_per_t = 0.0
    in_struct.flux_mgo_kg_per_t = 0.0
    in_struct.max_iterations = 0
    
    status = _lib.thermo_calculate_equilibrium(ctypes.byref(in_struct), ctypes.byref(out_struct))
    
    if status != 0:
        raise RuntimeError(f"C kernel returned error status: {status}")
        
    return {
        "phase_fractions": {PHASES[i]: out_struct.phase_fractions[i] for i in range(N_PHASES)},
        "phase_compositions": {
            PHASES[p]: {ELEMENTS[e]: out_struct.phase_compositions[p][e] for e in range(N_ELEMENTS) if out_struct.phase_compositions[p][e] > 1e-9}
            for p in range(N_PHASES)
        },
        "element_recovery": {ELEMENTS[e]: out_struct.element_recovery[e] for e in range(N_ELEMENTS)},
        "energy_delta_kj_per_kg": out_struct.energy_delta_kj_per_kg,
        "gibbs_free_energy": out_struct.gibbs_free_energy_kj_per_mol,
        "iterations_used": out_struct.iterations_used,
        "status": "OK"
    }