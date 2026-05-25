import re
from typing import Dict, Any

class AIArchitect:
    def __init__(self):
        # We use a mocked intelligence engine via keyword extraction
        # to focus on architecture synthesis without external LLM dependencies.
        pass

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Interprets user prompts and synthesizes architectural parameters, constraints,
        and technology presets.
        """
        prompt_lower = prompt.lower()
        
        # Default architecture spec
        spec = {
            "num_qubits": 16,
            "topology": "modular",
            "preset": "Research prototype",
            "density": "medium",
            "frequency_band": "5-7 GHz",
            "hard_constraints": [
                "Max substrate size: 10x10 mm",
                "Target frequency band: 5-7 GHz",
                "Layer count: 5"
            ],
            "soft_constraints": [
                "Minimize crosstalk",
                "Maintain symmetric routing where possible"
            ],
            "engineering_notes": "AI Architect analyzed prompt and selected default research modular layout."
        }

        # 1. Infer number of qubits
        match = re.search(r'(\d+)\s*(-?qubit|q)', prompt_lower)
        if match:
            spec["num_qubits"] = int(match.group(1))

        # 2. Technology Presets & Topology
        if "error correction" in prompt_lower or "surface" in prompt_lower:
            spec["preset"] = "Surface-code"
            spec["topology"] = "surface-code lattice"
            spec["density"] = "high"
            spec["soft_constraints"].append("Nearest-neighbor dense coupling preferred")
            spec["engineering_notes"] = "Inferred Surface-code topology for quantum error correction suitability."
        elif "ibm" in prompt_lower or "hex" in prompt_lower:
            spec["preset"] = "IBM-style"
            spec["topology"] = "heavy-hex"
            spec["density"] = "medium"
            spec["soft_constraints"].append("Hexagonal connectivity for reduced spectator qubit errors")
            spec["engineering_notes"] = "Inferred IBM-style heavy-hex lattice based on user prompt."
        elif "sycamore" in prompt_lower or "google" in prompt_lower or "grid" in prompt_lower:
            spec["preset"] = "Google-style"
            spec["topology"] = "grid"
            spec["density"] = "high"
            spec["soft_constraints"].append("Square grid coupling for maximum parallel gate depth")
            spec["engineering_notes"] = "Inferred Google Sycamore-style square grid topology."
        else:
            spec["preset"] = "Research prototype"
            spec["topology"] = "modular"
            spec["density"] = "sparse"
            spec["soft_constraints"].append("Clustered modular topology for isolated multi-qubit testing")
            spec["engineering_notes"] = "Inferred Research prototype layout (sparse modular) for standard scaling."

        # 3. Size constraints based on qubit count
        q = spec["num_qubits"]
        if q > 100:
            spec["hard_constraints"][0] = "Max substrate size: 20x20 mm"
            spec["soft_constraints"].append("High routing density anticipated")
        elif q > 50:
            spec["hard_constraints"][0] = "Max substrate size: 15x15 mm"
        
        # 4. Density adjustments from keywords
        if "low noise" in prompt_lower or "sparse" in prompt_lower or "low crosstalk" in prompt_lower:
            spec["density"] = "sparse"
            spec["soft_constraints"].append("Maximize physical distance between resonators")
            spec["engineering_notes"] += " Added low-noise (sparse) routing strategy."

        return spec

if __name__ == "__main__":
    architect = AIArchitect()
    print(architect.analyze_prompt("Design a scalable low-noise chip for quantum error correction with 64 qubits"))
