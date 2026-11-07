#include "thermo.h"
#include <math.h>
#include <string.h>

/* ---------- Element and phase names ---------- */
static const char* const ELEMENT_NAMES[N_ELEMENTS] = {
    [ELEM_FE] = "Fe", [ELEM_CU] = "Cu", [ELEM_AL] = "Al", [ELEM_ZN] = "Zn",
    [ELEM_PB] = "Pb", [ELEM_NI] = "Ni", [ELEM_CR] = "Cr", [ELEM_MN] = "Mn",
    [ELEM_SI] = "Si", [ELEM_C] = "C", [ELEM_O] = "O", [ELEM_S] = "S",
    [ELEM_P] = "P", [ELEM_SN] = "Sn", [ELEM_MG] = "Mg"
};

static const char* const PHASE_NAMES[N_PHASES] = {
    [PHASE_METAL] = "metal",
    [PHASE_SLAG] = "slag",
    [PHASE_GAS] = "gas"
};

/* ---------- STUB partition coefficients ----------
 * STUB_PARTITION[phase][element] = fraction of element mass reporting to phase.
 * Each element's three coefficients sum to 1.0.
 *
 * These are deliberate placeholders that satisfy the mass-balance invariant
 * and roughly mirror real behavior at steelmaking temperatures. Replace with
 * a Gibbs minimization or PINN surrogate later without changing the ABI.
 */
static const double STUB_PARTITION[N_PHASES][N_ELEMENTS] = {
    [PHASE_METAL] = {
        [ELEM_FE] = 1.0, [ELEM_CU] = 1.0, [ELEM_AL] = 1.0, [ELEM_ZN] = 1.0,
        [ELEM_PB] = 1.0, [ELEM_NI] = 1.0, [ELEM_CR] = 1.0, [ELEM_MN] = 1.0,
        [ELEM_SI] = 1.0, [ELEM_C] = 0.0, [ELEM_O] = 0.0, [ELEM_S] = 0.0,
        [ELEM_P] = 0.0, [ELEM_SN] = 1.0, [ELEM_MG] = 1.0,
    },
    [PHASE_SLAG] = {
        [ELEM_FE] = 0.0, [ELEM_CU] = 0.0, [ELEM_AL] = 0.0, [ELEM_ZN] = 0.0,
        [ELEM_PB] = 0.0, [ELEM_NI] = 0.0, [ELEM_CR] = 0.0, [ELEM_MN] = 0.0,
        [ELEM_SI] = 0.0, [ELEM_C] = 0.0, [ELEM_O] = 1.0, [ELEM_S] = 0.0,
        [ELEM_P] = 1.0, [ELEM_SN] = 0.0, [ELEM_MG] = 0.0,
    },
    [PHASE_GAS] = {
        [ELEM_FE] = 0.0, [ELEM_CU] = 0.0, [ELEM_AL] = 0.0, [ELEM_ZN] = 0.0,
        [ELEM_PB] = 0.0, [ELEM_NI] = 0.0, [ELEM_CR] = 0.0, [ELEM_MN] = 0.0,
        [ELEM_SI] = 0.0, [ELEM_C] = 1.0, [ELEM_O] = 0.0, [ELEM_S] = 1.0,
        [ELEM_P] = 0.0, [ELEM_SN] = 0.0, [ELEM_MG] = 0.0,
    },
};

/* ---------- Internal helpers ---------- */
static int validate_input(const ThermoInput* in)
{
    if (in == NULL) return THERMO_ERR_INPUT;
    
    double total = 0.0;
    for (int e = 0; e < N_ELEMENTS; e++) {
        if (in->composition[e] < 0.0) return THERMO_ERR_INPUT;
        total += in->composition[e];
    }
    if (fabs(total - 1.0) > 1e-3) return THERMO_ERR_INPUT;

    if (in->temperature <= 0.0) return THERMO_ERR_INPUT;
    if (in->pressure <= 0.0) return THERMO_ERR_INPUT;
    if (in->flux_cao_kg_per_t < 0.0 || in->flux_mgo_kg_per_t < 0.0)
        return THERMO_ERR_INPUT;
    
    return THERMO_OK;
}

static void compute_phase_partition(const ThermoInput* in, ThermoOutput* out)
{
    /* 
     * Dynamic Partitioning:
     * We start with the base STUB_PARTITION, but we dynamically shift 
     * elements into the gas phase based on the furnace temperature.
     */
    double dynamic_partition[N_PHASES][N_ELEMENTS];
    
    // Copy the base matrix
    for (int p = 0; p < N_PHASES; p++) {
        for (int e = 0; e < N_ELEMENTS; e++) {
            dynamic_partition[p][e] = STUB_PARTITION[p][e];
        }
    }

    /* 
     * Temperature Effect on Volatilization (Gas Phase)
     * At higher temperatures, volatile elements (Zn, Pb, Mg) vaporize.
     * A simple linear scaling is used: as T goes from 1000K to 2000K,
     * the fraction going to gas increases by up to 50%.
     */
    double temp_factor = (in->temperature - 1000.0) / 1000.0;
    if (temp_factor < 0.0) temp_factor = 0.0; // Below 1000K, no extra vaporization
    if (temp_factor > 1.0) temp_factor = 1.0; // Cap at 2000K

    int volatile_elements[] = {ELEM_ZN, ELEM_PB, ELEM_MG};
    int num_volatile = 3;

    for (int i = 0; i < num_volatile; i++) {
        int e = volatile_elements[i];
        // Shift a fraction of the metal phase into the gas phase
        double shift = dynamic_partition[PHASE_METAL][e] * 0.5 * temp_factor;
        
        dynamic_partition[PHASE_METAL][e] -= shift;
        dynamic_partition[PHASE_GAS][e] += shift;
    }

    /* Step 1: phase masses */
    for (int p = 0; p < N_PHASES; p++) {
        double mass = 0.0;
        for (int e = 0; e < N_ELEMENTS; e++) {
            mass += in->composition[e] * dynamic_partition[p][e];
        }
        out->phase_fractions[p] = mass;
    }

    /* Step 2: composition "within" each phase */
    for (int p = 0; p < N_PHASES; p++) {
        const double denom = out->phase_fractions[p];
        for (int e = 0; e < N_ELEMENTS; e++) {
            out->phase_compositions[p][e] = 
            (denom > 1e-12)
            ? (in->composition[e] * dynamic_partition[p][e]) / denom: 0.0;
        }
    }

    /* Step 3: element recovery into metal phase (now dynamic!) */
    for (int e = 0; e < N_ELEMENTS; e++) {
        out->element_recovery[e] = dynamic_partition[PHASE_METAL][e];
    }
    
    /* Step 4: Calculate a mock Energy Delta based on temperature */
    // Higher temperatures require more energy input
    out->energy_delta_kj_per_kg = (in->temperature - 298.15) * 0.05;
}

/* ---------- Public API ---------- */

int thermo_calculate_equilibrium(const ThermoInput* in, ThermoOutput* out)
{
    if (out == NULL) return THERMO_ERR_INPUT;

    /* Zero the output so partial runs leave a clean slate */
    memset(out, 0, sizeof(*out));

    int status = validate_input(in);
    if (status != THERMO_OK) {
        out->status = status;
        return status;
    }

    compute_phase_partition(in, out);

    /* Stub placeholders — replace with real thermodynamic model later */
    out->energy_delta_kj_per_kg       = 0.0;
    out->gibbs_free_energy_kj_per_mol = 0.0;
    out->iterations_used              = 1;
    out->status                       = THERMO_OK;

    return THERMO_OK;
}

int thermo_num_elements(void) { return N_ELEMENTS; }
int thermo_num_phases(void)   { return N_PHASES; }

const char* thermo_element_name(int index)
{
    if (index < 0 || index >= N_ELEMENTS) return NULL;
    return ELEMENT_NAMES[index];
}

const char* thermo_phase_name(int index)
{
    if (index < 0 || index >= N_PHASES) return NULL;
    return PHASE_NAMES[index];
}

const char* thermo_version(void) { return THERMO_VERSION_STRING; }