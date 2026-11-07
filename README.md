# ♻️ Circular Metals Flow Engine

**A Physics-Informed Scrap Optimizer for Industrial Symbiosis**

## 📌 The Waste Problem
The global metal recycling industry loses billions of dollars annually due to **compositional uncertainty** and **downcycling**. When complex scrap (like e-waste or end-of-life vehicles) is melted, without a precise understanding of the thermodynamics, valuable metals are lost to slag or vaporized into gas. Furthermore, the leftover slag is often sent to landfills because its exact composition is unknown.

## 💡 Our Solution
The **Circular Metals Flow Engine** is a decision-support tool that predicts metal recovery, calculates energy/CO₂ savings, and suggests valorization pathways for leftover slag. 

It uses a high-performance **C thermodynamic kernel** bound to **Python** to simulate the furnace environment. By adjusting the temperature and scrap composition, users can find the optimal processing parameters to maximize yield and minimize waste.

## 🏗️ Architecture
This project uses a modular, multi-language architecture:
1. **C Kernel (`c_kernel/`)**: Performs the heavy thermodynamic mass-balance and temperature-dependent phase partitioning.
2. **Python Bindings (`python/thermo_bindings.py`)**: Uses `ctypes` to bridge Python and C memory structures.
3. **Analysis Engine (`python/scrap_engine.py`)**: Calculates economic (USD saved) and environmental (CO₂ avoided) impact.
4. **Frontend (`app/`)**: A Streamlit dashboard for real-time interactive simulation.

## 🚀 How to Run Locally

### 1. Compile the C Kernel
You must compile the shared library before running the Python app. 
*   **Windows (x64)**: Open an x64 Native Tools Command Prompt, navigate to `c_kernel`, and run:
    ```bash
    cl /LD /O2 /W3 thermo.c /Fe:libthermo.dll
    ```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Dashboard
```bash
python -m streamlit run app/Home.py
```
## 🧪 Testing
 - **C Tests**: Compile and run `test_thermo.exe` or `./test_thermo`.
 - **Python Tests**: Run `python -m pytest python/test_bindings.py` or `python python/test_bindings.py`.

## 📊 Impact
By optimizing just one 1,000 kg batch of aluminum scrap, the engine demonstrates a savings of **30,131 kWh** of energy and 
**$6,019** in capital compared to virgin mining, while diverting slag to agricultural fertilizer or cement substitutes.