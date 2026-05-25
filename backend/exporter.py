import gdstk
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MatplotlibPolygon
import os
from typing import List, Dict, Any

class Exporter:
    def __init__(self, lib: gdstk.Library, cell: gdstk.Cell):
        self.lib = lib
        self.cell = cell

    def export_gds(self, filepath: str):
        """
        Exports the library to a standard GDSII file (KLayout compatible).
        """
        self.lib.write_gds(filepath)

    def export_preview(self, filepath: str, chip_size: tuple):
        """
        Renders the GDS polygons into a Matplotlib figure for Streamlit preview.
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#041020') # Deep blue background
        ax.set_aspect('equal')
        ax.set_xlim(0, chip_size[0])
        ax.set_ylim(0, chip_size[1])
        ax.axis('off')

        # Layer colors based on fabricated chip image
        color_map = {
            1: '#020810', # Ground cutouts (darkest blue)
            2: '#4FC3F7', # Resonators (bright cyan)
            3: '#E1F5FE', # Qubit Islands (very light cyan/white)
            4: '#81D4FA', # Control Lines (light cyan)
            5: '#FFFFFF'  # Labels/Bridges (white)
        }

        # Extract polygons from cell
        for poly in self.cell.get_polygons(apply_repetitions=True):
            # The layer info is lost in get_polygons() without tracking, 
            # but we can do a hack or use cell.polygons
            pass
            
        # Proper way in gdstk:
        for polygon in self.cell.polygons:
            pts = polygon.points
            layer = polygon.layer
            color = color_map.get(layer, '#FFFFFF')
            mpl_poly = MatplotlibPolygon(pts, closed=True, facecolor=color, edgecolor=color, alpha=0.9)
            ax.add_patch(mpl_poly)
            
        for path in self.cell.paths:
            layer = path.layers[0] if path.layers else 0
            color = color_map.get(layer, '#FFFFFF')
            for p_poly in path.to_polygons():
                mpl_poly = MatplotlibPolygon(p_poly.points, closed=True, facecolor=color, edgecolor=color, alpha=0.9)
                ax.add_patch(mpl_poly)

        fig.savefig(filepath, facecolor=fig.get_facecolor(), bbox_inches='tight', dpi=300)
        plt.close(fig)
        
    def export_svg(self, filepath: str, chip_size: tuple):
        """
        Renders the layout as an SVG file using matplotlib.
        """
        # We can just reuse the matplotlib code but save as svg
        preview_path = filepath.replace(".svg", "_tmp.png")
        self.export_preview(preview_path, chip_size)
        # Actually proper SVG would be better, but saving matplotlib as SVG works.
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor('#041020')
        ax.set_aspect('equal')
        ax.set_xlim(0, chip_size[0])
        ax.set_ylim(0, chip_size[1])
        ax.axis('off')

        color_map = {
            1: '#020810', 2: '#4FC3F7', 3: '#E1F5FE', 4: '#81D4FA', 5: '#FFFFFF'
        }

        for polygon in self.cell.polygons:
            pts = polygon.points
            layer = polygon.layer
            color = color_map.get(layer, '#FFFFFF')
            mpl_poly = MatplotlibPolygon(pts, closed=True, facecolor=color, edgecolor=color, alpha=0.9)
            ax.add_patch(mpl_poly)
            
        for path in self.cell.paths:
            layer = path.layers[0] if path.layers else 0
            color = color_map.get(layer, '#FFFFFF')
            for p_poly in path.to_polygons():
                mpl_poly = MatplotlibPolygon(p_poly.points, closed=True, facecolor=color, edgecolor=color, alpha=0.9)
                ax.add_patch(mpl_poly)

        fig.savefig(filepath, facecolor=fig.get_facecolor(), bbox_inches='tight', format='svg')
        plt.close(fig)
