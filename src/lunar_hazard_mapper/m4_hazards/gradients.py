"""
src/lunar_hazard_mapper/m4_hazards/gradients.py

DATA CONTRACT (not pre-defined by the scaffold — defined here, documented in
docs/api/DATA_CONTRACTS.md, open to review/change by the team):

    dem = {
        "z":  2D np.ndarray (float64), elevation in meters,
        "dx": float, meters per pixel in the x (column) direction,
        "dy": float, meters per pixel in the y (row) direction,
    }
    (optional keys "nodata", "crs" may be present and are ignored here --
    M4 does not own CRS handling, only M1/M3 do.)

Every m4_hazards function that takes `dem` expects exactly this shape.
`compute_gradients` is the only function that reads dx/dy directly; every
other m4_hazards function receives already-computed derivatives and never
re-reads dx/dy, so pixel spacing is threaded through exactly once.
"""
from __future__ import annotations
import numpy as np


def compute_gradients(dem: dict) -> dict:
    """Compute DEM gradients using central finite differences (handbook
    5.1/4.2): zx ~= [z(x+dx)-z(x-dx)]/(2*dx), zy ~= [z(y+dy)-z(y-dy)]/(2*dy).
    One-sided differences are used at the raster edges.

    Args:
        dem: {"z": ndarray[H,W], "dx": float, "dy": float}

    Returns:
        {"zx": ndarray[H,W], "zy": ndarray[H,W]}
    """
    z = np.asarray(dem["z"], dtype=np.float64)
    dx, dy = float(dem["dx"]), float(dem["dy"])

    zx = np.empty_like(z)
    zx[:, 1:-1] = (z[:, 2:] - z[:, :-2]) / (2.0 * dx)
    zx[:, 0] = (z[:, 1] - z[:, 0]) / dx
    zx[:, -1] = (z[:, -1] - z[:, -2]) / dx

    zy = np.empty_like(z)
    zy[1:-1, :] = (z[2:, :] - z[:-2, :]) / (2.0 * dy)
    zy[0, :] = (z[1, :] - z[0, :]) / dy
    zy[-1, :] = (z[-1, :] - z[-2, :]) / dy

    return {"zx": zx, "zy": zy}
