"""src/lunar_hazard_mapper/m4_hazards/hessian.py"""
from __future__ import annotations
import numpy as np


def compute_hessian(dem: dict) -> dict:
    """Construct H = [[zxx, zxy], [zyx, zyy]] via central finite differences
    (handbook 5.5/5.6). Returns the three independent components (zxx, zyy,
    zxy; zyx == zxy since H is symmetric).

    Args:
        dem: {"z": ndarray[H,W], "dx": float, "dy": float}

    Returns:
        {"zxx": ndarray, "zyy": ndarray, "zxy": ndarray}
    """
    z = np.asarray(dem["z"], dtype=np.float64)
    dx, dy = float(dem["dx"]), float(dem["dy"])

    zxx = np.empty_like(z)
    zxx[:, 1:-1] = (z[:, 2:] - 2 * z[:, 1:-1] + z[:, :-2]) / (dx ** 2)
    zxx[:, 0] = zxx[:, 1]
    zxx[:, -1] = zxx[:, -2]

    zyy = np.empty_like(z)
    zyy[1:-1, :] = (z[2:, :] - 2 * z[1:-1, :] + z[:-2, :]) / (dy ** 2)
    zyy[0, :] = zyy[1, :]
    zyy[-1, :] = zyy[-2, :]

    zxy = np.empty_like(z)
    zxy[1:-1, 1:-1] = (
        z[2:, 2:] - z[2:, :-2] - z[:-2, 2:] + z[:-2, :-2]
    ) / (4.0 * dx * dy)
    zxy[0, :] = zxy[1, :]
    zxy[-1, :] = zxy[-2, :]
    zxy[:, 0] = zxy[:, 1]
    zxy[:, -1] = zxy[:, -2]

    return {"zxx": zxx, "zyy": zyy, "zxy": zxy}
