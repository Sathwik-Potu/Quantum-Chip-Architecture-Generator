import gdstk
from typing import Dict, Any

class TransmonGenerator:
    def __init__(self, rules: Dict[str, float]):
        self.rules = rules

    def generate(self, cell: gdstk.Cell, x: float, y: float, layer: int = 3):
        """
        Generates a cross-style or pad-style transmon on the specified layer.
        """
        pad_size = self.rules.get("pad_size", 200.0)
        gap = self.rules.get("junction_width", 20.0)
        
        # Ground cutout (layer 1)
        pocket_size = pad_size + 150.0
        cutout = gdstk.rectangle(
            (x - pocket_size/2, y - pocket_size/2),
            (x + pocket_size/2, y + pocket_size/2),
            layer=1
        )
        cell.add(cutout)

        # Transmon cross island (X-mon style)
        cross_width = pad_size / 6
        cross_length = pad_size * 0.8
        
        # Center cross
        h_rect = gdstk.rectangle(
            (x - cross_length/2, y - cross_width/2),
            (x + cross_length/2, y + cross_width/2),
            layer=layer
        )
        v_rect = gdstk.rectangle(
            (x - cross_width/2, y - cross_length/2),
            (x + cross_width/2, y + cross_length/2),
            layer=layer
        )
        
        # Add capacitive pads at the ends of vertical arms
        cap_pad_width = pad_size * 0.7
        cap_pad_height = pad_size * 0.25
        
        top_cap = gdstk.rectangle(
            (x - cap_pad_width/2, y + cross_length/2),
            (x + cap_pad_width/2, y + cross_length/2 + cap_pad_height),
            layer=layer
        )
        
        bottom_cap = gdstk.rectangle(
            (x - cap_pad_width/2, y - cross_length/2 - cap_pad_height),
            (x + cap_pad_width/2, y - cross_length/2),
            layer=layer
        )
        
        cell.add(h_rect, v_rect, top_cap, bottom_cap)

    def generate_cpw_pad(self, cell: gdstk.Cell, x: float, y: float, orientation: str = 'N', layer: int = 4):
        """
        Generates a launch pad for CPW feedlines.
        """
        pad_width = 300.0
        pad_length = 400.0
        taper_length = 200.0
        trace_width = self.rules.get("trace_width", 10.0)
        
        # This is a simplified pad structure
        if orientation == 'N':
            pts = [
                (x - pad_width/2, y),
                (x + pad_width/2, y),
                (x + pad_width/2, y - pad_length),
                (x + trace_width/2, y - pad_length - taper_length),
                (x - trace_width/2, y - pad_length - taper_length),
                (x - pad_width/2, y - pad_length)
            ]
        elif orientation == 'S':
            pts = [
                (x - pad_width/2, y),
                (x + pad_width/2, y),
                (x + pad_width/2, y + pad_length),
                (x + trace_width/2, y + pad_length + taper_length),
                (x - trace_width/2, y + pad_length + taper_length),
                (x - pad_width/2, y + pad_length)
            ]
        elif orientation == 'E':
            pts = [
                (x, y - pad_width/2),
                (x, y + pad_width/2),
                (x - pad_length, y + pad_width/2),
                (x - pad_length - taper_length, y + trace_width/2),
                (x - pad_length - taper_length, y - trace_width/2),
                (x - pad_length, y - pad_width/2)
            ]
        else: # W
            pts = [
                (x, y - pad_width/2),
                (x, y + pad_width/2),
                (x + pad_length, y + pad_width/2),
                (x + pad_length + taper_length, y + trace_width/2),
                (x + pad_length + taper_length, y - trace_width/2),
                (x + pad_length, y - pad_width/2)
            ]
            
        pad = gdstk.Polygon(pts, layer=layer)
        cell.add(pad)
