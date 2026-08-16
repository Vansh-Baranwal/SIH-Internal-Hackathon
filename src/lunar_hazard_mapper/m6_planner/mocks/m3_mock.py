import numpy as np

class MockM3Provider:
    """
    Deterministic mock provider for M3 DEM (Digital Elevation Model) outputs.
    Ensures M6 (and Blender visualization) can run without waiting for actual M3 outputs.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def generate_synthetic_dem(self, width: int = 500, height: int = 500, resolution: float = 1.0) -> np.ndarray:
        """
        Generates a 2D numpy array representing a synthetic elevation map.
        
        Args:
            width: Number of columns (x)
            height: Number of rows (y)
            resolution: Meters per pixel
            
        Returns:
            2D numpy array of elevations in meters.
        """
        # Base flat terrain
        dem = np.zeros((height, width), dtype=np.float32)
        
        # Add basic large-scale sloping
        x = np.linspace(-width/2, width/2, width) * resolution
        y = np.linspace(-height/2, height/2, height) * resolution
        xv, yv = np.meshgrid(x, y)
        dem += 0.05 * xv + 0.02 * yv
        
        # Add some random high-frequency noise
        dem += self.rng.normal(0, 0.5, (height, width))
        
        return dem
