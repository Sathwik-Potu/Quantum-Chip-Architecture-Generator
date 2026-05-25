import gdstk
import numpy as np
from typing import Dict, Any, Tuple

class ResonatorGenerator:
    def __init__(self, rules: Dict[str, float]):
        self.rules = rules
        self.trace_width = rules.get("trace_width", 10.0)
        self.velocity = 1e8 # Approx propagation velocity in m/s on chip

    def estimate_length(self, target_frequency_ghz: float) -> float:
        """
        Approximates lambda/4 resonator length based on L = v / (4 * f).
        Frequency is in GHz. Returns length in um.
        """
        f = target_frequency_ghz * 1e9
        L_meters = self.velocity / (4 * f)
        return L_meters * 1e6 # convert to micrometers

    def generate_meander(self, cell: gdstk.Cell, start_pt: Tuple[float, float], end_pt: Tuple[float, float], frequency_ghz: float, layer: int = 2):
        """
        Generates a frequency-aware, smooth CPW meander resonator.
        """
        target_length = self.estimate_length(frequency_ghz)
        
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        dist = np.sqrt(dx**2 + dy**2)
        
        # Smooth rounded meander (matching the fabricated chip visuals)
        bend_radius = self.trace_width * 2.5
        path = gdstk.FlexPath(start_pt, self.trace_width, layer=layer, bend_radius=bend_radius)
        
        if dist >= target_length:
            path.interpolation([end_pt])
            cell.add(path)
            return
            
        ux, uy = dx/dist, dy/dist
        nx, ny = -uy, ux
        
        amplitude = 180.0
        num_meanders = int((target_length - dist) / (4 * amplitude)) + 1
        
        pts = [start_pt]
        step = dist / (num_meanders + 1)
        
        for i in range(num_meanders):
            base_x = start_pt[0] + ux * step * (i + 0.5)
            base_y = start_pt[1] + uy * step * (i + 0.5)
            
            p1 = (base_x - ux * step*0.25, base_y)
            p2 = (base_x - ux * step*0.25 + nx * amplitude, base_y + ny * amplitude)
            p3 = (base_x + ux * step*0.25 + nx * amplitude, base_y + ny * amplitude)
            p4 = (base_x + ux * step*0.25, base_y)
            
            pts.extend([p1, p2, p3, p4])
            
        pts.append(end_pt)
        
        for p in pts[1:]:
            path.segment(p)
            
        cell.add(path)
