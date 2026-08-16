"""src/lunar_hazard_mapper/m4_hazards/slope.py"""
from __future__ import annotations
import numpy as np


def compute_slope(gradients: dict) -> dict:
    """slope = arctan(sqrt(zx^2 + zy^2))  (handbook 5.1). Stores both units
    per numerical rule #1 (radians internally, degrees for display/thresholds).

    Args:
        gradients: output of gradients.compute_gradients -> {"zx":..., "zy":...}

    Returns:
        {"slope_rad": ndarray, "slope_deg": ndarray}
    """
    zx, zy = gradients["zx"], gradients["zy"]
    slope_rad = np.arctan(np.sqrt(zx ** 2 + zy ** 2))
    slope_deg = np.degrees(slope_rad)
    return {"slope_rad": slope_rad, "slope_deg": slope_deg}


def compute_aspect(gradients: dict) -> np.ndarray:
    """aspect = atan2(-zx, zy) (handbook 5.2). Not in the original scaffold
    stub list but required by the M4 formula checklist (§15) and the
    architecture diagram's terrain-analysis box -- added here since aspect
    is directly derived from the same gradients this module already owns."""
    zx, zy = gradients["zx"], gradients["zy"]
    return np.arctan2(-zx, zy)


def compute_surface_normal(gradients: dict) -> np.ndarray:
    """n = [-zx, -zy, 1] / sqrt(zx^2+zy^2+1) (handbook 5.3). Same rationale
    as compute_aspect: not an explicit scaffold stub, but owned by this
    module's inputs and required by the M4 formula checklist."""
    zx, zy = gradients["zx"], gradients["zy"]
    denom = np.sqrt(zx ** 2 + zy ** 2 + 1.0)
    return np.stack([-zx / denom, -zy / denom, 1.0 / denom], axis=-1)


def compute_roughness(dem: dict, window: int = 3) -> np.ndarray:
    """Local roughness sigma_z (handbook 5.4): sqrt(local variance) over a
    (window x window) neighbourhood. Window is configurable because
    roughness depends on scale (M4-C requirement)."""
    from scipy.ndimage import uniform_filter
    z = np.asarray(dem["z"], dtype=np.float64)
    if window < 3 or window % 2 == 0:
        raise ValueError("window must be an odd integer >= 3")
    mean_local = uniform_filter(z, size=window, mode="nearest")
    mean_sq_local = uniform_filter(z ** 2, size=window, mode="nearest")
    variance = np.clip(mean_sq_local - mean_local ** 2, 0.0, None)
    return np.sqrt(variance)


# --- Synthetic ridge/valley/bowl fixtures ---------------------------------
# These are required by the workflow's testing matrix (§11: "Synthetic ridge",
# "Synthetic bowl/valley" -> Hessian eigenstructure, owner M4) and by
# numerical rule #3 (unit-test flat/known-slope/ridge/valley/bowl), but the
# scaffold's synthetic/terrain/ only allocated flat.py, slope.py, crater.py,
# boulder.py, combined.py -- no dedicated ridge/valley/bowl file. Putting
# them alongside generate_slope() in synthetic/terrain/slope.py since they're
# all planar/linear terrain-shape fixtures, not discrete objects. Flag this
# for the team: if a teammate expects a separate file, these three functions
# move verbatim, no logic changes needed.
