#include "thermo.h"
#include <stdio.h>
#include <math.h>

static int failures = 0;

#define CHECK(cond, msg) do {                                    \
    if (!(cond)) { printf("FAIL: %s\n", msg); failures++; }      \
    else         { printf("ok:   %s\n", msg); }                  \
} while (0)

#define CHECK_NEAR(a, b, tol, msg) do {                          \
    if (fabs((a) - (b)) > (tol)) {                               \
        printf("FAIL: %s (got %.6g, expected %.6g)\n",           \
               msg, (double)(a), (double)(b));                   \
        failures++;                                              \
    } else { printf("ok:   %s\n", msg); }                        \
} while (0)

static void test_introspection(void)
{
    printf("\n--- test_introspection ---\n");
    CHECK(thermo_num_elements() == N_ELEMENTS, "thermo_num_elements matches enum");
    CHECK(thermo_num_phases()   == N_PHASES,   "thermo_num_phases matches enum");
    CHECK(thermo_element_name(ELEM_FE) != NULL, "known element -> non-NULL");
    CHECK(thermo_element_name(-1)      == NULL, "negative index   -> NULL");
    CHECK(thermo_element_name(N_ELEMENTS) == NULL, "out-of-range  -> NULL");
    CHECK(thermo_version() != NULL, "version string non-NULL");
}

static void test_pure_iron(void)
{
    printf("\n--- test_pure_iron ---\n");
    ThermoInput in = {0};
    ThermoOutput out = {0};

    in.composition[ELEM_FE] = 1.0;
    in.temperature = 1873.0;   /* 1600 C */
    in.pressure = 1.0;

    int status = thermo_calculate_equilibrium(&in, &out);
    CHECK(status == THERMO_OK, "returns THERMO_OK");
    CHECK_NEAR(out.phase_fractions[PHASE_METAL], 1.0, 1e-9, "metal  = 100%");
    CHECK_NEAR(out.phase_fractions[PHASE_SLAG],  0.0, 1e-9, "slag   = 0%");
    CHECK_NEAR(out.phase_fractions[PHASE_GAS],   0.0, 1e-9, "gas    = 0%");
    CHECK_NEAR(out.phase_compositions[PHASE_METAL][ELEM_FE], 1.0, 1e-9,
               "metal is pure Fe");
    CHECK_NEAR(out.element_recovery[ELEM_FE], 1.0, 1e-9, "Fe recovery = 1.0");
}

static void test_mixed_scrap(void)
{
    printf("\n--- test_mixed_scrap ---\n");
    ThermoInput in = {0};
    ThermoOutput out = {0};

    /* Low-alloy steel with tramp elements */
    in.composition[ELEM_FE] = 0.90;
    in.composition[ELEM_CU] = 0.02;
    in.composition[ELEM_C]  = 0.01;
    in.composition[ELEM_O]  = 0.04;
    in.composition[ELEM_S]  = 0.01;
    in.composition[ELEM_P]  = 0.02;
    in.temperature = 1873.0;
    in.pressure = 1.0;

    int status = thermo_calculate_equilibrium(&in, &out);
    CHECK(status == THERMO_OK, "returns THERMO_OK");

    /* Metal = Fe + Cu = 0.92
     * Slag  = O + P   = 0.06
     * Gas   = C + S   = 0.02 */
    CHECK_NEAR(out.phase_fractions[PHASE_METAL], 0.92, 1e-9, "metal = 0.92");
    CHECK_NEAR(out.phase_fractions[PHASE_SLAG],  0.06, 1e-9, "slag  = 0.06");
    CHECK_NEAR(out.phase_fractions[PHASE_GAS],   0.02, 1e-9, "gas   = 0.02");

    double total = out.phase_fractions[0]
                 + out.phase_fractions[1]
                 + out.phase_fractions[2];
    CHECK_NEAR(total, 1.0, 1e-9, "phase fractions sum to 1.0 (mass balance)");

    CHECK_NEAR(out.phase_compositions[PHASE_METAL][ELEM_FE], 0.90/0.92, 1e-9,
               "metal Fe fraction = 0.90/0.92");
    CHECK_NEAR(out.phase_compositions[PHASE_METAL][ELEM_CU], 0.02/0.92, 1e-9,
               "metal Cu fraction = 0.02/0.92");

    CHECK_NEAR(out.element_recovery[ELEM_FE], 1.0, 1e-9, "Fe recovery = 1.0");
    CHECK_NEAR(out.element_recovery[ELEM_O],  0.0, 1e-9, "O  recovery = 0.0");
    CHECK_NEAR(out.element_recovery[ELEM_C],  0.0, 1e-9, "C  recovery = 0.0");
}

static void test_invalid_input(void)
{
    printf("\n--- test_invalid_input ---\n");
    ThermoInput in = {0};
    ThermoOutput out = {0};

    in.composition[ELEM_FE] = 0.5;   /* sums to 0.5, should be rejected */
    in.temperature = 1873.0;
    in.pressure = 1.0;

    int status = thermo_calculate_equilibrium(&in, &out);
    CHECK(status == THERMO_ERR_INPUT, "unnormalized composition rejected");
    CHECK(out.status == THERMO_ERR_INPUT, "status field set on failure");
}

int main(void)
{
    printf("thermo kernel version: %s\n", thermo_version());
    test_introspection();
    test_pure_iron();
    test_mixed_scrap();
    test_invalid_input();

    printf("\n%s (%d failure%s)\n",
           failures == 0 ? "ALL TESTS PASSED" : "SOME TESTS FAILED",
           failures, failures == 1 ? "" : "s");
    return failures == 0 ? 0 : 1;
}