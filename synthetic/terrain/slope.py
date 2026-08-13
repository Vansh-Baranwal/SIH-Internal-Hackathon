import numpy as np


def generate_slope(size=256, pixel_size_m=1.0, slope_deg=5.0, base_elevation_m=0.0):
    """
    Generate a synthetic SLOPED PLANE terrain elevation grid.

    Synthetic test data only -- used to test the M3 DEM pipeline against a
    known, exact slope value (useful later for checking M4's slope math).

    Args:
        size: number of pixels per side (grid is size x size).
        pixel_size_m: ground sampling distance per pixel, in meters.
        slope_deg: constant slope angle in degrees, rising along +x (east).
        base_elevation_m: elevation at x=0 (meters).

    Returns:
        dict with "elevation" (2D float32 array), "pixel_size_m",
        "source_type" ("synthetic"), and "slope_deg" (the known ground
        truth slope used to generate it, for validation later).
    """
    x_indices = np.arange(size, dtype=np.float32) * pixel_size_m
    rise_per_meter = np.tan(np.deg2rad(slope_deg))
    row = base_elevation_m + x_indices * rise_per_meter
    elevation = np.tile(row, (size, 1)).astype(np.float32)

    return {
        "elevation": elevation,
        "pixel_size_m": pixel_size_m,
        "source_type": "synthetic",
        "slope_deg": slope_deg,
    }
