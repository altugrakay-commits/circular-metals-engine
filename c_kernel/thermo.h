#ifndef THERMO_H
#define THERMO_H

#ifdef __cplusplus
extern "C" {
#endif

/* =====================================================================
 * Circular Metals Flow Engine — C Thermodynamics Kernel
 * ---------------------------------------------------------------------
 * This header defines the ABI contract between the C kernel and the
 * Python bindings. Do NOT reorder fields or change types without
 * updating python/thermo_bindings.py.
 * ===================================================================== */
#define THERMO_VERSION_STRING "0.1.0-stub"

/* ---------- DLL Export Macro for Windows ---------- */
#ifdef _WIN32
    #define THERMO_API __declspec(dllexport)
#else
    #define THERMO_API
#endif

/* ---------- Element indices ---------- */
enum Element {
    ELEM_FE = 0,    /* Iron */
    ELEM_CU,        /* Copper */
    ELEM_AL,        /* Aluminum */
    ELEM_ZN,        /* Zinc */
    ELEM_PB,        /* Lead */
    ELEM_NI,        /* Nickel */
    ELEM_CR,        /* Chromium */
    ELEM_MN,        /* Manganese */
    ELEM_SI,        /* Silicon */
    ELEM_C,         /* Carbon */
    ELEM_O,         /* Oxygen */
    ELEM_S,         /* Sulfur */
    ELEM_P,         /* Phosphorus */
    ELEM_SN,        /* Tin */
    ELEM_MG,        /* Magnesium */
    N_ELEMENTS
};

/* ---------- Phase indices ---------- */
enum Phase {
    PHASE_METAL = 0,
    PHASE_SLAG,
    PHASE_GAS,
    N_PHASES
};

/* ---------- Status codes ---------- */
#define THERMO_OK                0
#define THERMO_ERR_INPUT        -1  /* invalid input (e.g. composition not normalized) */
#define THERMO_ERR_NOCONV       -2  /* solver did not converge */
#define THERMO_ERR_INTERNAL     -3  /* unexpected internal failure */

/* ---------- Input struct ----------
 * composition:           mass fractions, must sum to 1.0 within 1e-3
 * temperature:           Kelvin (> 0)
 * pressure:              atm (> 0)
 * flux_cao_kg_per_t:     slag former addition; 0 = none
 * flux_mgo_kg_per_t:     slag former addition; 0 = none
 * max_iterations:        solver iteration budget; 0 = engine default
 */

 typedef struct {
    double composition[N_ELEMENTS];
    double temperature;
    double pressure;
    double flux_cao_kg_per_t;
    double flux_mgo_kg_per_t;
    int max_iterations;
 } ThermoInput;

/* ---------- Output struct ----------
 * phase_fractions:              mass fraction of each phase; sums to 1.0
 * phase_compositions[p][e]:     mass fraction of e *within* phase p;
 *                               sums to 1.0 for each p with non-zero mass
 * element_recovery[e]:          fraction of element e reporting to metal
 * energy_delta_kj_per_kg:       net energy balance (negative = exothermic)
 * gibbs_free_energy_kj_per_mol: total Gibbs free energy at solution
 * iterations_used:              number of solver iterations
 * status:                       one of THERMO_OK / THERMO_ERR_*
 */

 typedef struct {
    double phase_fractions[N_PHASES];
    double phase_compositions[N_PHASES][N_ELEMENTS];
    double element_recovery[N_ELEMENTS];
    double energy_delta_kj_per_kg;
    double gibbs_free_energy_kj_per_mol;
    int iterations_used;
    int status;
 } ThermoOutput;

 /* ---------- Public API ---------- */

 /* Run the equilibrium / partition calculation. Returns status code. */
 THERMO_API int thermo_calculate_equilibrium(const ThermoInput* in, ThermoOutput* out);

 /* Introspection - used by Python bindings to validate sizes at import. */
 THERMO_API int thermo_num_elements(void);
 THERMO_API int thermo_num_phases(void);

 /* Name Lookups - return NULL on out-of-range index. */
 THERMO_API const char* thermo_element_name(int index);
 THERMO_API const char* thermo_phase_name(int index);

 /* Library version string. */
 THERMO_API const char* thermo_version(void);

 #ifdef __cplusplus
}
#endif
#endif /* THERMO_H */