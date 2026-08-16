import numpy as np

from synthetic.terrain.flat import generate_flat_terrain
from synthetic.terrain.slope import generate_slope
from synthetic.terrain.crater import generate_crater
from synthetic.terrain.boulder import generate_boulder


def generate_combined(size=256, pixel_size_m=1.0, slope_deg=2.0,
                       crater_center=None, boulder_centers=None):
    """
    Generate a synthetic COMBINED terrain: a gentle base slope, one crater,
    and a few boulders on top -- a more realistic test scene than any single
    feature alone.

    Synthetic test data only. Built by summing the simpler generators in
    this package, so it stays consistent with them (same elevation-grid
    shape and metadata keys).

    Args:
        size: number of pixels per side (grid is size x size).
        pixel_size_m: ground sampling distance per pixel, in meters.
        slope_deg: gentle base slope angle in degrees.
        crater_center: (row, col) pixel center for the crater; defaults to
            grid center.
        boulder_centers: list of (row, col) pixel centers for boulders;
            defaults to two boulders placed away from the crater.

    Returns:
        dict with "elevation" (2D float32 array), "pixel_size_m",
        "source_type" ("synthetic"), and "features" describing what was
        placed (for validation / ground-truth comparison).
    """
    base = generate_slope(size=size, pixel_size_m=pixel_size_m,
                           slope_deg=slope_deg, base_elevation_m=0.0)
    elevation = base["elevation"].copy()

    if crater_center is None:
        crater_center = (size // 2, size // 2)
    crater = generate_crater(size=size, pixel_size_m=pixel_size_m,
                              radius_px=max(4, size // 8),
                              depth_m=5.0, rim_height_m=1.0,
                              center=crater_center)
    elevation += crater["elevation"]

    if boulder_centers is None:
        boulder_centers = [
            (size // 4, size // 4),
            (3 * size // 4, 3 * size // 4),
        ]
    boulder_radius = max(2, size // 32)
    for bc in boulder_centers:
        boulder = generate_boulder(size=size, pixel_size_m=pixel_size_m,
                                    radius_px=boulder_radius, height_m=1.0,
                                    center=bc)
        elevation += boulder["elevation"]

    elevation = elevation.astype(np.float32)

    return {
        "elevation": elevation,
        "pixel_size_m": pixel_size_m,
        "source_type": "synthetic",
        "features": {
            "slope_deg": slope_deg,
            "crater_center_px": crater_center,
            "crater_radius_px": crater["radius_px"],
            "boulder_centers_px": boulder_centers,
            "boulder_radius_px": boulder_radius,
        },
    }
