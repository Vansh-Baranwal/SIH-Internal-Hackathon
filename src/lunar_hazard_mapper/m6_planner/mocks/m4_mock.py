import numpy as np

class MockM4Provider:
    """
    Deterministic mock provider for M4 Hazard & Confidence outputs.
    Ensures M6 can visualize hazard layers in Blender without waiting for M4.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def generate_hazard_map(self, width: int = 500, height: int = 500) -> dict:
        """
        Generates synthetic 2D arrays for slope, craters, boulders, and overall confidence.
        
        Returns:
            Dictionary containing 2D numpy arrays.
        """
        # Slope in degrees (typically 0 to 30)
        slope = self.rng.uniform(0.0, 15.0, (height, width)).astype(np.float32)
        
        # Boolean masks or probability maps for craters/boulders
        craters = self.rng.random((height, width)) < 0.05
        boulders = self.rng.random((height, width)) < 0.02
        
        # Confidence map (0.0 to 1.0)
        confidence = self.rng.uniform(0.6, 1.0, (height, width)).astype(np.float32)
        
        # Introduce a low confidence zone in the center
        cy, cx = height // 2, width // 2
        y, x = np.ogrid[:height, :width]
        dist_sq = (x - cx)**2 + (y - cy)**2
        low_conf_mask = dist_sq < (50**2)
        confidence[low_conf_mask] *= 0.5
        
        return {
            "slope": slope,
            "craters": craters.astype(np.float32),
            "boulders": boulders.astype(np.float32),
            "confidence": confidence
        }
