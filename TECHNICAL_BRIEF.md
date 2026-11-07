
# Technical Brief: Circular Metals Flow Engine

## 1. System Architecture
The application is decoupled into four distinct layers to ensure high performance and testability:
*   **The C Kernel**: Executes an array-based mass balance across three phases (Metal, Slag, Gas) for 15 elements. It uses a dynamic partition matrix where volatile elements (Zn, Mg, Pb) shift from the metal phase to the gas phase linearly as the furnace temperature increases from 1000 K to 2000 K.
*   **The Bindings**: Implemented via `ctypes`, mapping Python dictionaries to C-structs (`ThermoInput` and `ThermoOutput`), ensuring zero-copy memory access.
*   **The Analysis Engine**: Computes the energy delta (MJ) by comparing the recovered mass of each element against industrial baselines for virgin ore mining vs. secondary recycling. Converts this to CO₂ avoided and USD saved.
*   **The UI**: A Streamlit front-end that provides real-time feedback on composition changes and temperature variations.

## 2. Thermodynamic Model (C Kernel)
For a given composition, $C$, and temperature, $T$, the phase mass, $M_p$ for phase, $p$, is calculated as:

$$M_p = \sum_{e} C_e \cdot P_{p,e}(T)$$

Where $P_{p,e}(T)$ is the temperature-dependent partition coefficient.

For volatile elements (Zn, Mg), the partition to gas is defined as:

$$P_{gas,e}(T) = P_{gas,e, base} + \left( P_{metal,e, base} \cdot 0.5 \cdot \max\left(0, \min\left(1, \frac{T - 1000}{1000}\right)\right) \right)$$

## 3. Economic & Environmental Calculations
*   **Energy Saved (kWh)**: 
    $$E_{saved} = \sum_{e} (M_{recovered, e} \cdot (E_{virgin, e} - E_{recycled, e})) \times 0.2778$$
*   **CO₂ Avoided (kg)**: Uses a standard global grid average of $0.4$ kg CO₂ / kWh.
*   **Capital Saved (USD)**: Uses a standard industrial electricity rate of $ 0.15 / kWh.

## 4. Leftover Valorization Logic
The Python `leftover_advisor` parses the resulting Slag composition:
*   If `O > 30%` and `Si > 10%` -> Cement Substitute (SCM).
*   If `P > 5%` -> Agricultural Fertilizer.
*   If `Fe > 15%` -> Road Base / Aggregate.
*   Fallback -> Landfill (flagged for flux addition).