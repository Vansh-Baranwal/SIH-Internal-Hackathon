"""synthetic/terrain/flat.py"""
import numpy as np


def generate_flat_terrain(shape=(64, 64), elevation=1000.0, dx=1.0, dy=1.0) -> dict:
    """Mandatory fixture per numerical rule #3 / handbook 4.4: flat DEM,
    used to verify slope -> 0 deg exactly."""
    z = np.full(shape, elevation, dtype=np.float64)
    return {"z": z, "dx": dx, "dy": dy}
