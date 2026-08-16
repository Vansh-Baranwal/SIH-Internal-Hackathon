"""src/lunar_hazard_mapper/m4_hazards/boulder.py"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from skimage import morphology, measure


def detect_boulders(dem: dict, min_height: float = 0.15, min_area_px: int = 3,
                     max_area_px: int = 500, background_window: int = 15) -> list[dict]:
    """Elevation-anomaly baseline (handbook 5.8, spec M4-K). The scaffold's
    fixed signature is detect_boulders(dem) only -- no image/shadow
    parameters -- so this returns geometric-evidence-only candidates.

    IMPORTANT: per M4-L / critical warning #4, "never use shadow alone as
    proof" -- and by the same logic, don't call these heights final without
    an independent check either. Cross-checking against shadow.detect_shadows()
    output (height = shadow_length * tan(sun_elevation)) is the caller's job:
    compose detect_boulders(dem) + detect_shadows(dem, sun_angle) yourself
    and fuse in fusion.fuse_hazards() if you need the cross-checked height.
    That composition is NOT done inside this function because the scaffold
    signature doesn't accept a sun angle here.

    Args:
        dem: {"z": ndarray, "dx": float, "dy": float}

    Returns:
        list of dicts: {id, center_row, center_col, height_m, radius_px,
        radius_m, hazard_radius_m, confidence}
    """
    z = np.asarray(dem["z"], dtype=np.float64)
    dx = float(dem["dx"])

    background = ndimage.median_filter(z, size=background_window, mode="nearest")
    anomaly = z - background
    mask = anomaly > min_height
    labeled, _ = ndimage.label(mask)

    candidates = []
    for region in measure.regionprops(labeled, intensity_image=anomaly):
        if region.area < min_area_px or region.area > max_area_px:
            continue
        rows, cols = np.where(labeled == region.label)
        height = float(anomaly[rows, cols].max())
        radius_px = float(np.sqrt(region.area / np.pi))
        confidence = float(np.clip(0.4 + 0.6 * min(1.0, region.area / min_area_px / 3.0), 0.0, 1.0))

        candidates.append({
            "id": len(candidates),
            "center_row": float(region.centroid[0]), "center_col": float(region.centroid[1]),
            "height_m": height, "radius_px": radius_px, "radius_m": radius_px * dx,
            "hazard_radius_m": radius_px * dx * 1.5,  # safety margin for M5's leg/footprint clearance
            "confidence": confidence,
        })
    return candidates
