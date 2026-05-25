import gdstk
from typing import List, Tuple, Dict, Any
import numpy as np

class RoutingEngine:
    def __init__(self, rules: Dict[str, float]):
        self.rules = rules

    def generate_feedline(self, cell: gdstk.Cell, chip_size: Tuple[float, float], layer: int = 4):
        """
        Generates a multiplexed readout feedline.
        """
        margin = 1000.0
        width = chip_size[0]
        height = chip_size[1]
        
        path = gdstk.FlexPath((margin, height/2), self.rules.get("trace_width", 10.0), layer=layer)
        # Add slight wobble to feedline to avoid perfect straight lines
        path.interpolation([
            (width/3, height/2 + 200),
            (2*width/3, height/2 - 200),
            (width - margin, height/2)
        ])
        cell.add(path)

    def route_control_line(self, cell: gdstk.Cell, target_pt: Tuple[float, float], chip_size: Tuple[float, float], layer: int = 4):
        """
        Routes an XY/Z control line from edge of chip to qubit.
        """
        # Find closest edge
        x, y = target_pt
        d_left = x
        d_right = chip_size[0] - x
        d_bottom = y
        d_top = chip_size[1] - y
        
        min_d = min(d_left, d_right, d_bottom, d_top)
        
        if min_d == d_left:
            start_pt = (200.0, y)
        elif min_d == d_right:
            start_pt = (chip_size[0] - 200.0, y)
        elif min_d == d_bottom:
            start_pt = (x, 200.0)
        else:
            start_pt = (x, chip_size[1] - 200.0)
            
        path = gdstk.FlexPath(start_pt, self.rules.get("trace_width", 10.0)/2, layer=layer)
        # Basic orthogonal routing
        mid_pt = ((start_pt[0] + x)/2, (start_pt[1] + y)/2)
        path.segment((start_pt[0], mid_pt[1]))
        path.segment((x, y))
        cell.add(path)
