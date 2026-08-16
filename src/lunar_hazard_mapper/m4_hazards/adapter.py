"""
M3 -> M4 Boundary Adapter

Implements the documented M3->M4 contract by adapting the canonical M3 DEM object
into the dictionary structure expected by M4's hazard analysis pipeline.

Mapping:
M3 DEM.elevation    -> M4 input["z"]
M3 DEM.pixel_size_m -> M4 input["dx"]
M3 DEM.pixel_size_m -> M4 input["dy"]
"""
import numpy as np


def dem_to_m4_input(dem):
    """
    Adapts an M3 DEM object into the M4 input contract.

    Args:
        dem: An M3 DEM instance (from src.lunar_hazard_mapper.m3_terrain.dem)

    Returns:
        dict: The structure expected by M4 functions (e.g. compute_gradients), containing:
            "z": 2D float64 array of elevation in meters
            "dx": float, meters per pixel in x
            "dy": float, meters per pixel in y
            "origin": dict with "x_m" and "y_m" if a transform is present
    """
    m4_input = {
        "z": np.asarray(dem.elevation, dtype=np.float64),
        "dx": float(dem.pixel_size_m),
        "dy": float(dem.pixel_size_m),
    }

    # Extract origin from M3 transform if available
    if hasattr(dem, "transform") and dem.transform is not None:
        m4_input["origin"] = {
            "x_m": float(dem.transform.c),
            "y_m": float(dem.transform.f),
        }

    return m4_input
