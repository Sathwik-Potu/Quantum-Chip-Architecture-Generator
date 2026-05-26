# QuantumChip AI

![QuantumChip AI Banner](https://img.shields.io/badge/Status-Active-success.svg) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0%2B-FF4B4B) ![Qiskit](https://img.shields.io/badge/Qiskit-1.0.0%2B-6929C4)

**QuantumChip AI** is an advanced Quantum Electronic Design Automation (EDA) and simulation platform. It bridges the gap between high-level natural language intent and low-level physical hardware specifications by combining Generative AI with procedural geometry and quantum simulation.

---

## Features

- **AI-Powered Prompt Parsing:** Type natural language requests like *"Design a scalable 24-qubit high-performance QEC processor"*. The integrated **Groq LLaMA-3 Engine** instantly extracts implied physics and hardware constraints via JSON inference.
- **Procedural CAD Synthesis:** No static image assets. The application procedurally generates high-fidelity lithography masks using vector mathematics, drawing complete XMON transmons, interdigitated capacitive (IDC) couplers, and frequency-varied $\lambda/4$ meander readout resonators.
- **Quantum Circuit Simulation:** Automatically constructs quantum circuits tailored to your architectural focus (e.g., GHZ states, Bell states, QFT) and simulates realistic gate errors and coherence decay using **IBM Qiskit's AerSimulator**.
- **Real-time Dashboard:** A responsive Streamlit frontend provides instant telemetry on Qubit Fidelity, Power Consumption, and T1 Coherence Decay over time.

---

## Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/QuantumChip-AI.git
cd QuantumChip-AI
pip install -r requirements.txt
```

### 2. Configure Environment
QuantumChip AI uses the Groq inference engine for near-instant semantic parsing. 
1. Get a free API key from [Groq Console](https://console.groq.com/).
2. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Add your key to the `.env` file:
   ```env
   GROQ_API_KEY=gsk_your_api_key_here
   ```

### 3. Run the Dashboard
```bash
streamlit run app.py
```

---

## System Architecture

QuantumChip AI operates on a modular pipeline cleanly separating simulation, rendering, and UI logic:

| Module | Responsibility |
|---|---|
| `app.py` | **Frontend.** Handles Streamlit state management, chat interface, Plotly interactive rendering, and metric dashboarding. |
| `utils/chip_engine.py` | **AI Parser.** Interfaces with the Groq API (fallback to Regex) to map user text to a rigid physical `design` specification dict. |
| `utils/chip_layout.py` | **CAD Generator.** Mathematical engine that dynamically floorplans scalable topologies (Linear, Lattice, Surface-Code) and draws CPW trenches. |
| `utils/quantum_circuit.py` | **Simulator.** Connects to Qiskit. Translates fidelity specs into noise models, runs circuits, and returns measurement probability distributions. |

---

## Visual Aesthetics

The generated layouts are designed to mimic real-world superconducting processor lithography:
- **XMON Pockets:** Etched cross profiles with distinct center metal islands and Josephson junction markings.
- **Impedance-Matched Routing:** Filleted corners (circular arcs) on all coplanar waveguides to prevent microwave signal reflection.
- **Multiplexed Readout:** 24+ qubit scaling introduces shared CPW readout buses.

---

## Contributing

Contributions are welcome. Please feel free to submit a Pull Request if you have ideas for improving the procedural generation algorithms, adding trapped-ion support, or enhancing the Qiskit noise models.

---

## License
MIT License. See `LICENSE` for more information.
