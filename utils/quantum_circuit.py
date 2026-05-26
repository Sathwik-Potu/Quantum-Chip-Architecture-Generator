"""
quantum_circuit.py — Builds and runs Qiskit quantum circuits.
Falls back to synthetic counts if Qiskit/Aer is unavailable.
"""

import math
import random
import numpy as np


def run_circuit(design: dict, shots: int = 2048) -> dict:
    """Run the quantum circuit for a chip design. Returns measurement counts."""
    n = min(design["n_qubits"], 8)
    ctype = design["circuit"]

    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator
        from qiskit.compiler import transpile

        qc = QuantumCircuit(n, n)

        if ctype == "Bell State":
            for i in range(0, n - 1, 2):
                qc.h(i)
                qc.cx(i, i + 1)
        elif ctype == "GHZ":
            qc.h(0)
            for i in range(n - 1):
                qc.cx(i, i + 1)
        elif ctype == "QFT":
            for i in range(n):
                qc.h(i)
                for j in range(i + 1, n):
                    qc.cp(math.pi / (2 ** (j - i)), j, i)
        elif ctype == "Variational":
            for i in range(n):
                qc.ry(math.pi / 4, i)
            for i in range(n - 1):
                qc.cx(i, i + 1)
            for i in range(n):
                qc.rz(math.pi / 3, i)
        else:
            for i in range(n):
                qc.h(i)

        qc.measure(range(n), range(n))
        sim = AerSimulator()
        counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
        circuit_text = str(qc.draw(output="text"))
        return {"counts": counts, "circuit_text": circuit_text, "real": True, "n": n}

    except Exception:
        ns = min(2**n, 16)
        states = random.sample([format(i, f"0{n}b") for i in range(2**n)], ns)
        w = np.random.dirichlet(np.ones(ns) * 1.5) * shots
        counts = {s: int(v) for s, v in zip(states, w) if int(v) > 0}
        return {"counts": counts, "circuit_text": None, "real": False, "n": n}
