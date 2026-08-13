"""synthetic/terrain/combined.py"""
import numpy as np


def generate_combined(shape=(200, 200), dx=1.0, dy=1.0, seed=7) -> dict:
    """Composite 'landing corridor' DEM: rolling background + craters +
    boulder field + regional slope. Used for the M4 end-to-end demo/scripts."""
    rng = np.random.default_rng(seed)
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]

    z = np.zeros(shape, dtype=np.float64)
    for _ in range(8):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        amp, sigma = rng.uniform(-3.0, 3.0), rng.uniform(20, 50)
        r2 = (xx - cx) ** 2 + (yy - cy) ** 2
        z += amp * np.exp(-r2 / (2 * sigma ** 2))
    z += np.tan(np.radians(3.0)) * xx * dx  # mild regional slope

    crater_gt = []
    for cy_f, cx_f, diam, depth, rimh in [
        (0.25, 0.30, 26, 6.0, 1.2), (0.65, 0.70, 40, 9.5, 1.8), (0.55, 0.20, 14, 3.0, 0.7)]:
        cy, cx = cy_f * h, cx_f * w
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        radius_px = diam / 2.0
        floor = -depth * np.exp(-(r ** 2) / (2 * (radius_px * 0.6) ** 2))
        rim = rimh * np.exp(-((r - radius_px) ** 2) / (2 * (radius_px * 0.15) ** 2))
        z += floor + rim
        crater_gt.append({"center_row": cy, "center_col": cx, "diameter_px": diam,
                           "diameter_m": diam * dx, "depth_m": depth, "rim_height_m": rimh})

    boulder_gt = []
    for _ in range(10):
        cy, cx = rng.uniform(10, h - 10), rng.uniform(10, w - 10)
        height, radius_px = rng.uniform(0.4, 1.8), rng.uniform(1.5, 4.0)
        r2 = (xx - cx) ** 2 + (yy - cy) ** 2
        z += height * np.exp(-r2 / (2 * radius_px ** 2))
        boulder_gt.append({"center_row": cy, "center_col": cx, "height_m": height,
                            "radius_px": radius_px, "radius_m": radius_px * dx})

    return {"z": z, "dx": dx, "dy": dy,
            "ground_truth": {"craters": crater_gt, "boulders": boulder_gt}}
