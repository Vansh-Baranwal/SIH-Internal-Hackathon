"""src/lunar_hazard_mapper/m4_hazards/curvature.py"""
from __future__ import annotations
from .hessian import compute_hessian


def compute_curvature(dem: dict) -> dict:
    """Second-order curvature descriptors (handbook 5.6):
        K = det(H) = zxx*zyy - zxy^2        (Gaussian-style curvature)
        H_mean = (zxx + zyy) / 2            (mean-curvature-style)
    Calls hessian.compute_hessian internally so callers only need `dem`,
    matching the scaffold's fixed compute_curvature(dem) signature -- this
    intentionally duplicates zero logic with hessian.py, it composes it.

    Args:
        dem: {"z": ndarray, "dx": float, "dy": float}

    Returns:
        {"zxx","zyy","zxy": ndarray (passed through for eigenfeatures.py),
         "gaussian_curvature": ndarray, "mean_curvature": ndarray}
    """
    h = compute_hessian(dem)
    K = h["zxx"] * h["zyy"] - h["zxy"] ** 2
    H_mean = (h["zxx"] + h["zyy"]) / 2.0
    return {**h, "gaussian_curvature": K, "mean_curvature": H_mean}
