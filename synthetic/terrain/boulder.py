"""synthetic/terrain/boulder.py"""
import numpy as np


def generate_boulder(shape=(128, 128), n_boulders=6, height_range=(0.3, 1.5),
                      radius_range_px=(2.0, 5.0), dx=1.0, dy=1.0, seed=42,
                      base_elevation=0.0) -> dict:
    """Scatter Gaussian-bump boulders on a flat base. Returns dem-dict plus
    "ground_truth" list (one dict per planted boulder)."""
    rng = np.random.default_rng(seed)
    h, w = shape
    z = np.full(shape, base_elevation, dtype=np.float64)
    yy, xx = np.mgrid[0:h, 0:w]
    ground_truth = []
    margin = int(max(radius_range_px) * 3)
    for _ in range(n_boulders):
        cy = rng.uniform(margin, h - margin)
        cx = rng.uniform(margin, w - margin)
        height = rng.uniform(*height_range)
        radius_px = rng.uniform(*radius_range_px)
        r2 = (xx - cx) ** 2 + (yy - cy) ** 2
        z += height * np.exp(-r2 / (2 * radius_px ** 2))
        ground_truth.append({
            "center_row": float(cy), "center_col": float(cx),
            "height_m": float(height), "radius_px": float(radius_px),
            "radius_m": float(radius_px * dx),
        })
    return {"z": z, "dx": dx, "dy": dy, "ground_truth": ground_truth}
