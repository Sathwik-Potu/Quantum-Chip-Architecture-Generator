import gdstk
from typing import Dict, Any, Tuple

from backend.topology_engine import TopologyEngine
from backend.transmon_generator import TransmonGenerator
from backend.resonator_generator import ResonatorGenerator
from backend.routing_engine import RoutingEngine
from backend.optimizer import Optimizer
from backend.validator import Validator
from backend.exporter import Exporter

class FabricationLayout:
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.rules = {
            "trace_width": 10.0,
            "gap_width": 6.0,
            "resonator_pitch": 50.0,
            "coupler_gap": 15.0,
            "pad_size": 250.0,
            "ground_clearance": 50.0,
            "junction_width": 20.0
        }
        
        self.lib = gdstk.Library()
        self.cell = self.lib.new_cell('QUANTUM_CHIP')
        
    def generate(self) -> Tuple[str, str, str, Dict[str, Any]]:
        """
        Orchestrates the entire generation process.
        Returns paths to generated files and validation metadata.
        """
        # 1. Topology Generation
        topo_engine = TopologyEngine(self.spec)
        layout_data = topo_engine.generate_layout()
        positions = layout_data["qubit_positions"]
        connections = layout_data["connections"]
        chip_size = layout_data["chip_size"]
        
        # 2. Optimization Phase (Procedural Noise & Spacing)
        optimizer = Optimizer(self.spec)
        positions = optimizer.apply_procedural_noise(positions)
        positions = optimizer.optimize_spacing(positions)
        
        # 3. Ground plane cutout (simplified as a large background polygon on Layer 1)
        ground_plane = gdstk.rectangle((0, 0), chip_size, layer=1)
        self.cell.add(ground_plane)
        
        # 4. Routing Engine (Feedlines & Control Lines)
        routing_engine = RoutingEngine(self.rules)
        routing_engine.generate_feedline(self.cell, chip_size, layer=4)
        
        transmon_gen = TransmonGenerator(self.rules)
        resonator_gen = ResonatorGenerator(self.rules)
        
        # 5. Place Qubits (Transmons) and control lines
        for x, y in positions:
            transmon_gen.generate(self.cell, x, y, layer=3)
            # Route an XY control line to each qubit
            routing_engine.route_control_line(self.cell, (x, y), chip_size, layer=4)
            
        # 6. Place Resonators (Coupling and Readout)
        freq_range = [5.0, 7.0]
        import random
        
        for i, j in connections:
            pt1 = positions[i]
            pt2 = positions[j]
            # Use random freq for each coupler for visual distinction
            freq = random.uniform(*freq_range)
            # Add gap for capacitive coupling instead of connecting directly
            gap = self.rules["coupler_gap"]
            # Simplified: just shorten the segment slightly
            dx, dy = pt2[0] - pt1[0], pt2[1] - pt1[1]
            dist = (dx**2 + dy**2)**0.5
            if dist > 2*gap:
                ux, uy = dx/dist, dy/dist
                start_pt = (pt1[0] + ux * gap, pt1[1] + uy * gap)
                end_pt = (pt2[0] - ux * gap, pt2[1] - uy * gap)
                resonator_gen.generate_meander(self.cell, start_pt, end_pt, frequency_ghz=freq, layer=2)

        # 7. Add Labels & Air Bridges (Visual only)
        label = gdstk.text(f"CHIP: {self.spec['preset']}", 300, (200, chip_size[1] - 500), layer=5)
        self.cell.add(*label)
        
        # Add edge connectors (CPW launch pads)
        transmon_gen.generate_cpw_pad(self.cell, chip_size[0]/2, 0, 'S', layer=4)
        transmon_gen.generate_cpw_pad(self.cell, chip_size[0]/2, chip_size[1], 'N', layer=4)
        
        # 8. Export & Validate
        exporter = Exporter(self.lib, self.cell)
        
        # Ensure output directory exists
        import os
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
            
        gds_path = "outputs/chip_layout.gds"
        png_path = "outputs/chip_layout.png"
        svg_path = "outputs/chip_layout.svg"
        
        exporter.export_gds(gds_path)
        exporter.export_preview(png_path, chip_size)
        exporter.export_svg(svg_path, chip_size)
        
        validator = Validator(self.spec)
        metadata = validator.validate()
        
        return gds_path, png_path, svg_path, metadata
