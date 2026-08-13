"""synthetic/terrain/slope.py"""
import numpy as np


def generate_slope(shape=(64, 64), angle_deg=5.0, dx=1.0, dy=1.0, direction="x") -> dict:
    """Mandatory fixture: perfectly planar surface tilted at exactly
    `angle_deg`, used to verify compute_slope() recovers the known angle."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    grad = np.tan(np.radians(angle_deg))
    z = grad * (xx * dx if direction == "x" else yy * dy)
    return {"z": z.astype(np.float64), "dx": dx, "dy": dy}


# --- Added beyond the scaffold stub ---------------------------------------
# The workflow's testing matrix (§11) requires "Synthetic ridge" and
# "Synthetic bowl/valley" fixtures, owned by M4, but scaffold_repo.py did
# not allocate a dedicated file for them. Placed here alongside
# generate_slope() since they're all planar/linear terrain-shape fixtures
# (as opposed to crater.py/boulder.py's discrete-object fixtures). If the
# team wants a separate ridge.py/bowl.py, these three functions move
# verbatim -- no logic changes needed.

def generate_ridge(shape=(64, 64), height=20.0, width_px=10.0, dx=1.0, dy=1.0) -> dict:
    """Linear ridge along y, centered in x. Hessian should show negative
    curvature across the ridge crest."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx = w / 2.0
    z = height * np.exp(-((xx - cx) ** 2) / (2 * width_px ** 2))
    return {"z": z.astype(np.float64), "dx": dx, "dy": dy}


def generate_valley(shape=(64, 64), depth=20.0, width_px=10.0, dx=1.0, dy=1.0) -> dict:
    """Inverse of generate_ridge(): a linear valley (positive curvature trough)."""
    d = generate_ridge(shape, height=depth, width_px=width_px, dx=dx, dy=dy)
    return {"z": -d["z"], "dx": dx, "dy": dy}


def generate_bowl(shape=(64, 64), depth=15.0, radius_px=15.0, dx=1.0, dy=1.0) -> dict:
    """Radially symmetric depression (paraboloid). Both Hessian eigenvalues
    should be positive near the center."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = h / 2.0, w / 2.0
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    z = -depth * np.exp(-r2 / (2 * radius_px ** 2))
    return {"z": z.astype(np.float64), "dx": dx, "dy": dy}
