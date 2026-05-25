import numpy as np
from typing import List, Tuple, Dict, Any

class TopologyEngine:
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.num_qubits = spec["num_qubits"]
        self.topology = spec["topology"]
        
        # Base chip size logic
        self.chip_size_x = 10000.0  # 10 mm
        self.chip_size_y = 10000.0
        if self.num_qubits > 50:
            self.chip_size_x = 15000.0
            self.chip_size_y = 15000.0
        if self.num_qubits > 100:
            self.chip_size_x = 20000.0
            self.chip_size_y = 20000.0

        # Density controls margin and pitch
        self.margin = 1500.0
        if spec.get("density") == "sparse":
            self.margin = 2500.0
        elif spec.get("density") == "high":
            self.margin = 1000.0

    def generate_layout(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing qubit positions and intended connections.
        Positions are (x, y) tuples.
        Connections are pairs of qubit indices (i, j).
        """
        positions = []
        connections = []

        if self.topology in ["grid", "surface-code lattice"]:
            positions, connections = self._generate_grid()
        elif self.topology == "heavy-hex":
            positions, connections = self._generate_heavy_hex()
        elif self.topology == "modular":
            positions, connections = self._generate_modular()
        else:
            # Fallback
            positions, connections = self._generate_grid()

        # Scale or center if needed
        # (This can be added later if generation isn't perfectly centered)
        
        return {
            "chip_size": (self.chip_size_x, self.chip_size_y),
            "qubit_positions": positions,
            "connections": connections
        }

    def _generate_grid(self) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]]]:
        cols = int(np.ceil(np.sqrt(self.num_qubits)))
        rows = int(np.ceil(self.num_qubits / cols))
        
        usable_x = self.chip_size_x - 2 * self.margin
        usable_y = self.chip_size_y - 2 * self.margin
        
        pitch_x = usable_x / max(1, cols - 1)
        pitch_y = usable_y / max(1, rows - 1)

        # To avoid making it too stretched if very few qubits
        pitch = min(pitch_x, pitch_y)
        if self.spec.get("density") == "sparse":
            pitch = max(pitch, 1500.0) # minimum sparse pitch

        positions = []
        connections = []
        
        # Center the grid
        grid_width = (cols - 1) * pitch
        grid_height = (rows - 1) * pitch
        start_x = (self.chip_size_x - grid_width) / 2
        start_y = (self.chip_size_y - grid_height) / 2

        count = 0
        grid_map = {}
        for r in range(rows):
            for c in range(cols):
                if count >= self.num_qubits:
                    break
                x = start_x + c * pitch
                y = start_y + r * pitch
                positions.append((x, y))
                grid_map[(r, c)] = count
                
                # Connect to left neighbor
                if c > 0 and (r, c-1) in grid_map:
                    connections.append((count, grid_map[(r, c-1)]))
                # Connect to bottom neighbor
                if r > 0 and (r-1, c) in grid_map:
                    connections.append((count, grid_map[(r-1, c)]))
                
                count += 1
                
        return positions, connections

    def _generate_heavy_hex(self) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]]]:
        # A simplified heavy hex generation (nodes on a hexagonal lattice with extra edge nodes)
        # For simplicity, we approximate a heavy-hex by building a honeycomb and placing qubits on vertices and edges.
        # This implementation falls back to a sparse grid with diagonal missing links if proper heavy-hex is too complex.
        # Here we do a brick-wall style which is topologically equivalent to honeycomb, then add edge qubits.
        
        # Due to complexity, we'll implement a staggered grid that mimics heavy hex connectivity
        positions = []
        connections = []
        
        cols = int(np.ceil(np.sqrt(self.num_qubits)))
        rows = int(np.ceil(self.num_qubits / cols))
        pitch = 1000.0
        if self.spec.get("density") == "sparse":
            pitch = 1500.0

        grid_width = (cols - 1) * pitch
        grid_height = (rows - 1) * pitch
        start_x = (self.chip_size_x - grid_width) / 2
        start_y = (self.chip_size_y - grid_height) / 2

        count = 0
        grid_map = {}
        for r in range(rows):
            for c in range(cols):
                if count >= self.num_qubits:
                    break
                # stagger
                offset = (pitch / 2) if r % 2 == 1 else 0
                x = start_x + c * pitch + offset
                y = start_y + r * pitch * 0.866 # sqrt(3)/2
                positions.append((x, y))
                grid_map[(r, c)] = count
                
                # Heavy hex has degree 2 or 3.
                # Left connection
                if c > 0 and (r, c-1) in grid_map:
                    connections.append((count, grid_map[(r, c-1)]))
                # Diagonal connection
                if r > 0:
                    if r % 2 == 1: # Odd row
                        if (r-1, c) in grid_map:
                            connections.append((count, grid_map[(r-1, c)]))
                    else: # Even row
                        if (r-1, c-1) in grid_map:
                            connections.append((count, grid_map[(r-1, c-1)]))
                            
                count += 1
                
        return positions, connections

    def _generate_modular(self) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int]]]:
        positions = []
        connections = []
        
        # Clusters of up to 4 qubits
        cluster_size = 4
        num_clusters = int(np.ceil(self.num_qubits / cluster_size))
        
        cluster_radius = 800.0
        global_radius = min(self.chip_size_x, self.chip_size_y) / 2 - self.margin - cluster_radius
        
        center_x = self.chip_size_x / 2
        center_y = self.chip_size_y / 2
        
        count = 0
        cluster_centers = []
        
        for c in range(num_clusters):
            if num_clusters == 1:
                cx, cy = center_x, center_y
            else:
                angle = 2 * np.pi * c / num_clusters
                cx = center_x + global_radius * np.cos(angle)
                cy = center_y + global_radius * np.sin(angle)
            cluster_centers.append((cx, cy))
            
            cluster_nodes = []
            qubits_in_this_cluster = min(cluster_size, self.num_qubits - count)
            for q in range(qubits_in_this_cluster):
                q_angle = 2 * np.pi * q / qubits_in_this_cluster
                qx = cx + cluster_radius * np.cos(q_angle)
                qy = cy + cluster_radius * np.sin(q_angle)
                positions.append((qx, qy))
                cluster_nodes.append(count)
                
                # Connect in a ring or star within cluster
                if q > 0:
                    connections.append((count, count - 1))
                if q == qubits_in_this_cluster - 1 and qubits_in_this_cluster > 2:
                    connections.append((count, count - q))
                
                count += 1
                
            # Inter-cluster connections
            if c > 0:
                # Connect the first node of this cluster to the last node of the previous cluster
                connections.append((cluster_nodes[0], cluster_nodes[0] - 1))
                
        return positions, connections
