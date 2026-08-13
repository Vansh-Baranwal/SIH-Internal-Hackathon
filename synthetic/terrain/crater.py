"""synthetic/terrain/crater.py"""
import numpy as np


def generate_crater(shape=(128, 128), diameter_px=30.0, depth=8.0, rim_height=1.5,
                     dx=1.0, dy=1.0, base_elevation=0.0, center=None) -> dict:
    """Simplified bowl-with-raised-rim crater model. Returns dem-dict plus
    "ground_truth" for recovery-tolerance tests (handbook 5.7)."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h / 2.0, w / 2.0) if center is None else center
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    radius_px = diameter_px / 2.0

    floor = -depth * np.exp(-(r ** 2) / (2 * (radius_px * 0.6) ** 2))
    rim = rim_height * np.exp(-((r - radius_px) ** 2) / (2 * (radius_px * 0.15) ** 2))
    z = base_elevation + floor + rim

    ground_truth = {
        "center_row": float(cy), "center_col": float(cx),
        "diameter_px": float(diameter_px), "diameter_m": float(diameter_px * dx),
        "depth_m": float(depth), "rim_height_m": float(rim_height),
    }
    return {"z": z.astype(np.float64), "dx": dx, "dy": dy, "ground_truth": ground_truth}
