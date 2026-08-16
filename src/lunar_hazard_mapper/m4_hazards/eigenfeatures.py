"""src/lunar_hazard_mapper/m4_hazards/eigenfeatures.py"""
from __future__ import annotations
import numpy as np


def compute_eigenfeatures(hessian: dict) -> dict:
    """Closed-form 2x2 symmetric eigendecomposition (handbook 5.6):
        l1,2 = (zxx+zyy +/- sqrt((zxx-zyy)^2 + 4*zxy^2)) / 2   (l1 >= l2)
    Eigenvectors solved analytically per-pixel; degenerate cells (perfectly
    flat/isotropic, zxy==0 and zxx==zyy) default to the canonical basis.

    Args:
        hessian: output of hessian.compute_hessian -> {"zxx","zyy","zxy"}

    Returns:
        {"l1": ndarray, "l2": ndarray,
         "principal_dir1": ndarray[H,W,2], "principal_dir2": ndarray[H,W,2]}
    """
    zxx, zyy, zxy = hessian["zxx"], hessian["zyy"], hessian["zxy"]

    trace = zxx + zyy
    disc = np.sqrt(np.clip((zxx - zyy) ** 2 + 4 * zxy ** 2, 0.0, None))
    l1 = (trace + disc) / 2.0
    l2 = (trace - disc) / 2.0

    vx1 = zxy.copy()
    vy1 = l1 - zxx
    norm1 = np.sqrt(vx1 ** 2 + vy1 ** 2)
    degenerate = norm1 < 1e-12
    vx1 = np.where(degenerate, 1.0, vx1)
    vy1 = np.where(degenerate, 0.0, vy1)
    norm1 = np.where(degenerate, 1.0, norm1)
    vx1, vy1 = vx1 / norm1, vy1 / norm1
    vx2, vy2 = -vy1, vx1  # orthogonal, since H is symmetric

    return {
        "l1": l1, "l2": l2,
        "principal_dir1": np.stack([vx1, vy1], axis=-1),
        "principal_dir2": np.stack([vx2, vy2], axis=-1),
    }
