"""src/lunar_hazard_mapper/m4_hazards/shadow.py"""
from __future__ import annotations
import numpy as np


def detect_shadows(image, sun_angle: float, sun_azimuth_deg: float = 135.0,
                    max_search_px: int = 40, brightness_percentile: float = 15.0) -> np.ndarray:
    """Shadow detection (handbook 5.8, spec M4-M). Two modes, auto-selected
    by the type of `image`, because the fixed scaffold signature
    detect_shadows(image, sun_angle) doesn't carry a DEM/brightness flag:

    1. `image` is a dem-dict {"z","dx","dy"} -> horizon raycast: for each
       cell, march toward the sun and test whether upstream terrain
       occludes it (theta_z = pi/2 - sun_angle, handbook 5.8). This is the
       geometrically correct mode and should be preferred once a real DEM
       exists.
    2. `image` is a plain 2D array (optical brightness/reflectance, no dx/dy
       available) -> intensity-threshold fallback: pixels below
       `brightness_percentile` are flagged shadowed. This only exists
       because M1/M2 haven't delivered real illumination-tagged imagery
       yet; it is a placeholder, not a claim that brightness alone proves
       shadow (critical warning #4 -- shadow != hazard either way).

    Args:
        image: dem-dict OR 2D ndarray of brightness/reflectance values
        sun_angle: solar elevation angle in degrees

    Returns:
        boolean ndarray, True = shadowed
    """
    if isinstance(image, dict) and "z" in image:
        return _horizon_shadow(image, sun_angle, sun_azimuth_deg, max_search_px)
    arr = np.asarray(image, dtype=np.float64)
    threshold = np.percentile(arr, brightness_percentile)
    return arr <= threshold


def _horizon_shadow(dem: dict, sun_elevation_deg: float, sun_azimuth_deg: float,
                     max_search_px: int) -> np.ndarray:
    z = np.asarray(dem["z"], dtype=np.float64)
    dx, dy = float(dem["dx"]), float(dem["dy"])
    h, w = z.shape
    elev_rad = np.radians(sun_elevation_deg)
    az_rad = np.radians(sun_azimuth_deg)
    dir_row, dir_col = -np.cos(az_rad), np.sin(az_rad)
    tan_elev = np.tan(elev_rad)
    if tan_elev <= 1e-6:
        return np.ones_like(z, dtype=bool)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    shadow = np.zeros_like(z, dtype=bool)
    for step in range(1, max_search_px + 1):
        src_row, src_col = yy - dir_row * step, xx - dir_col * step
        valid = (src_row >= 0) & (src_row < h) & (src_col >= 0) & (src_col < w)
        sr = np.clip(src_row, 0, h - 1).astype(int)
        sc = np.clip(src_col, 0, w - 1).astype(int)
        ground_dist = step * np.sqrt((dir_row * dy) ** 2 + (dir_col * dx) ** 2)
        required_height = z + ground_dist * tan_elev
        shadow |= valid & (z[sr, sc] > required_height)
    return shadow


def solar_zenith_deg(sun_elevation_deg: float) -> float:
    """theta_z = pi/2 - alpha (handbook 5.8)."""
    return 90.0 - sun_elevation_deg
