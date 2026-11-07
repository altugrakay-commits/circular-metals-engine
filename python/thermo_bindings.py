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
        ("iterations_used", ctypes.c_int)
    ]

# =====================================================================
# 2. Load the shared library
# =====================================================================

def _load_library():
    # Locate the library relative to this script.
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Determine extensions based on OS.
    if platform.system() == "Windows":
        lib_name = "libthermo.dll"
    elif platform.system() == "Darwin": # macOS
        lib_name = "libthermo.dylib"
    else:
        lib_name = "libthermo.so"

    # Assuming the python folder and c_kernel folder are siblings.
    lib_path = os.path.join(current_dir, "..", "c_kernel", lib_name)

    if not os.path.exists(lib_path):
        raise FileNotFoundError(f"Unable to find the compiled C library at: {lib_path}")

    lib = ctypes.CDLL(lib_path)

    lib.thermo_calculate_equilibrium.argtypes = [ctypes.POINTER(ThermoInput), ctypes.POINTER(ThermoOutput)]
    lib.thermo_calculate_equilibrium.restype = ctypes.c_int

    return lib

# Load it once the module is imported.
_lib = _load_library()

# =====================================================================
# 3. The Pythonic Wrapper
# =====================================================================

def calculate_equilibrium(composition_dict: dict, temperature: float, pressure: float = 1.0) -> dict:
    """
    Takes a dictionary of elements (e.g., {"Fe": 0.9, "Cu": 0.1}),
    runs the C engine, and returns a Python dictionary of the results.
    """
    in_struct = ThermoInput()
    out_struct = ThermoOutput()

    # 1. Map the dictionary to the C array.
    total_composition = 0.0
    for idx, elem in enumerate(ELEMENTS):
        val = composition_dict.get(elem, 0.0)
        in_struct.composition[idx] = val
        total_composition += val

    # Simple validation before sending to C.
    if abs(total_composition - 1.0) > 1e-3:
        raise ValueError(f"Composition must sum to 1.0, got {total_composition:.4f}")

    in_struct.temperature = temperature
    in_struct.pressure = pressure
    in_struct.flux_cao_kg_per_t = 0.0
    in_struct.flux_mgo_kg_per_t = 0.0
    in_struct.max_iterations = 0

    # 2. Call the C function
    status = _lib.thermo_calculate_equilibrium(ctypes.byref(in_struct), ctypes.byref(out_struct))

    if status != 0:
        raise RuntimeError(f"C kernel returned error status: {status}")

    # 3. Map the C output back to a Python dictionary.
    result = {
        "phase_fractions": {PHASES[i]: out_struct.phase_fractions[i] for i in range(N_PHASES)},
        "phase_compositions": {PHASES[p]: {ELEMENTS[e]: out_struct.phase_compositions[p][e] for e in range(N_ELEMENTS)
            if out_struct.phase_compositions[p][e] > 1e-9}
            for p in range(N_PHASES)
            },
        "element_recovery": {ELEMENTS[e]: out_struct.element_recovery[e] for e in range(N_ELEMENTS)},
        "energy_delta_kj_per_kg": out_struct.energy_delta_kj_per_kg,
        "gibbs_free_energy": out_struct.gibbs_free_energy_kj_per_mol,
        "iterations_used": out_struct.iterations_used,
        "status": "OK"
    }

    return result