"""
chip_engine.py — Quantum chip design logic.
Parses a plain-English prompt and returns a full chip specification dict using Groq LLM.
"""

import random
import re
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Attempt to load Groq client
try:
    from groq import Groq
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
except ImportError:
    groq_client = None

def _regex_fallback_engine(prompt: str) -> dict:
    p = prompt.lower()

    match = re.search(r"(\d+)\s*[-\s]?\s*(qubit|bit|qubits|bits)", p)
    n_qubits = max(1, min(int(match.group(1)), 100)) if match else 4
    low_power = any(w in p for w in ["low power", "low-power", "iot", "battery", "wearable", "energy"])
    hi_perf = any(w in p for w in ["high performance", "fast", "hpc", "server", "supercomputer", "accelerator"])
    ai_focus = any(w in p for w in ["ai", "machine learning", "ml", "neural", "deep learning", "inference"])
    crypto = any(w in p for w in ["crypto", "encryption", "security", "quantum key", "qkd"])
    comm = any(w in p for w in ["communication", "network", "teleportation", "entangle"])

    return _build_spec(prompt, n_qubits, low_power, hi_perf, ai_focus, crypto, comm)


def _llm_groq_engine(prompt: str) -> dict:
    system_prompt = """
    You are a world-class Quantum Computing architect. 
    Analyze the following user prompt for a quantum processor design.
    Extract the implied requirements and return ONLY a valid JSON object.
    
    If the user mentions "scalable QEC" (Quantum Error Correction), you must infer that they need a high performance chip with AT LEAST 24 qubits (surface code compatible).
    
    The JSON must have the following boolean or integer keys:
    - "n_qubits" (integer, 1 to 100. Default 4 if unspecified, but use physics intuition if terms like QEC or scalable are used).
    - "low_power" (boolean)
    - "hi_perf" (boolean)
    - "ai_focus" (boolean)
    - "crypto" (boolean)
    - "comm" (boolean)
    """

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    try:
        data = json.loads(response.choices[0].message.content)
        n_qubits = max(1, min(int(data.get("n_qubits", 4)), 100))
        low_power = bool(data.get("low_power", False))
        hi_perf = bool(data.get("hi_perf", False))
        ai_focus = bool(data.get("ai_focus", False))
        crypto = bool(data.get("crypto", False))
        comm = bool(data.get("comm", False))
        
        return _build_spec(prompt, n_qubits, low_power, hi_perf, ai_focus, crypto, comm)
    except Exception as e:
        print(f"Groq parsing failed: {e}. Falling back to Regex.")
        return _regex_fallback_engine(prompt)


def _build_spec(prompt, n_qubits, low_power, hi_perf, ai_focus, crypto, comm):
    process_nm = 3 if hi_perf else (7 if ai_focus else 14)
    temp_mk = 15 if hi_perf else (20 if ai_focus else 50)
    freq_ghz = 5.5 if hi_perf else (4.2 if ai_focus else (1.8 if low_power else 3.0))
    t1_us = 300 if hi_perf else (150 if ai_focus else (80 if low_power else 120))
    t2_us = int(t1_us * 0.7)
    gate_err = 0.001 if hi_perf else (0.003 if ai_focus else 0.005)
    fidelity = round((1 - gate_err) * 100, 2)
    power_mw = int(n_qubits * (2 if low_power else (8 if hi_perf else 5)))

    if ai_focus:
        qubit_type = "Transmon Superconducting"
    elif crypto:
        qubit_type = "Topological"
    elif comm:
        qubit_type = "Photonic"
    else:
        qubit_type = "Transmon Superconducting"

    err_correct = "Surface Code" if n_qubits >= 8 else ("Repetition Code" if n_qubits >= 4 else "None")

    if comm:
        circuit = "Bell State"
    elif crypto:
        circuit = "QFT"
    elif ai_focus:
        circuit = "Variational"
    elif hi_perf:
        circuit = "GHZ"
    else:
        circuit = "Superposition"

    complexity = "high" if (hi_perf or n_qubits >= 8) else ("low" if (low_power or n_qubits <= 2) else "medium")

    spec = {
        "Qubit Technology": qubit_type,
        "Qubit Count": f"{n_qubits} logical qubits",
        "Process Node": f"{process_nm} nm",
        "Operating Temp": f"{temp_mk} mK",
        "Clock Frequency": f"{freq_ghz} GHz",
        "Gate Fidelity": f"{fidelity}%",
        "T1 Coherence": f"{t1_us} µs",
        "T2 Coherence": f"{t2_us} µs",
        "Gate Error Rate": f"{gate_err:.4f}",
        "Error Correction": err_correct,
        "Power Budget": f"{power_mw} mW",
    }
    
    if ai_focus:
        spec["Quantum Volume"] = str(int(n_qubits * fidelity / 10))
    if crypto:
        spec["Key Rate"] = f"{int(n_qubits * 1.2)} kbps"

    qubit_comps = [
        {
            "name": f"Q{i}",
            "type": "qubit",
            "fidelity": fidelity - random.uniform(0, 1.5),
            "t1_us": t1_us + random.randint(-20, 20),
            "power_mw": power_mw / n_qubits,
        }
        for i in range(n_qubits)
    ]

    return {
        "prompt": prompt,
        "n_qubits": n_qubits,
        "qubits_type": qubit_type,
        "fidelity": fidelity,
        "t1_us": t1_us,
        "t2_us": t2_us,
        "gate_err": gate_err,
        "power_mw": power_mw,
        "freq_ghz": freq_ghz,
        "temp_mk": temp_mk,
        "err_correct": err_correct,
        "qubit_comps": qubit_comps,
        "spec": spec,
        "circuit": circuit,
        "complexity": complexity,
        "ai_focus": ai_focus,
        "hi_perf": hi_perf,
        "low_power": low_power,
        "crypto": crypto,
    }


def design_quantum_chip(prompt: str) -> dict:
    if groq_client is not None:
        try:
            return _llm_groq_engine(prompt)
        except Exception as e:
            print(f"Groq API Error: {e}")
            return _regex_fallback_engine(prompt)
    else:
        return _regex_fallback_engine(prompt)
