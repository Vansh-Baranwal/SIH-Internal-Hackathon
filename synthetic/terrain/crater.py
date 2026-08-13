import numpy as np


def generate_crater(size=256, pixel_size_m=1.0, radius_px=40,
                     depth_m=5.0, rim_height_m=1.0, center=None):
    """
    Generate a synthetic CRATER-LIKE terrain: a bowl depression with a
    raised rim, on an otherwise flat base.

    Synthetic test data only -- a simplified geometric approximation, not a
    physically simulated impact crater. Useful for testing M4's future
    crater-detection logic against a known ground-truth crater location.

    Args:
        size: number of pixels per side (grid is size x size).
        pixel_size_m: ground sampling distance per pixel, in meters.
        radius_px: crater radius in pixels.
        depth_m: depth of the bowl at its center, in meters (positive value,
                 terrain dips down by this much).
        rim_height_m: height of the raised rim above the flat base, in meters.
        center: (row, col) pixel center of the crater; defaults to grid center.

    Returns:
        dict with "elevation" (2D float32 array), "pixel_size_m",
        "source_type" ("synthetic"), and the crater parameters used
        ("center_px", "radius_px", "depth_m", "rim_height_m") for validation.
    """
    if center is None:
        center = (size // 2, size // 2)
    cy, cx = center

    yy, xx = np.mgrid[0:size, 0:size]
    dist_px = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    norm_dist = dist_px / radius_px  # 0 at center, 1 at rim

    # Parabolic bowl inside the crater radius.
    bowl = -depth_m * np.clip(1.0 - norm_dist ** 2, 0.0, None)

    # Raised rim as a smooth ring just outside the bowl (Gaussian ring).
    rim = rim_height_m * np.exp(-((norm_dist - 1.0) ** 2) / (2 * 0.15 ** 2))
    rim = np.where(norm_dist >= 1.0, rim, 0.0)

    elevation = (bowl + rim).astype(np.float32)

    return {
        "elevation": elevation,
        "pixel_size_m": pixel_size_m,
        "source_type": "synthetic",
        "center_px": center,
        "radius_px": radius_px,
        "depth_m": depth_m,
        "rim_height_m": rim_height_m,
    }
