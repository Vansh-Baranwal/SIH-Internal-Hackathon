import numpy as np


def generate_flat_terrain(size=256, pixel_size_m=1.0, elevation_m=0.0):
    """
    Generate a synthetic FLAT terrain elevation grid.

    This is synthetic test data only -- it does NOT represent real lunar
    elevation. It exists to test the M3 DEM pipeline (construction, export,
    validation) with the simplest possible case.

    Args:
        size: number of pixels per side (grid is size x size).
        pixel_size_m: ground sampling distance per pixel, in meters.
        elevation_m: constant elevation value (meters) for every cell.

    Returns:
        dict with:
            "elevation": 2D numpy array (float32) of shape (size, size),
                         every value equal to elevation_m.
            "pixel_size_m": pixel size used.
            "source_type": "synthetic" (never real measured data).
    """
    elevation = np.full((size, size), elevation_m, dtype=np.float32)

    return {
        "elevation": elevation,
        "pixel_size_m": pixel_size_m,
        "source_type": "synthetic",
    }
