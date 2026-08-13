import numpy as np


def generate_boulder(size=256, pixel_size_m=1.0, radius_px=8,
                      height_m=1.0, center=None):
    """
    Generate a synthetic BOULDER-LIKE terrain feature: a single raised,
    dome-shaped bump on an otherwise flat base.

    Synthetic test data only -- a simplified geometric approximation, not a
    real boulder. Useful for testing M4's future boulder-detection logic
    against a known ground-truth boulder location/size.

    Args:
        size: number of pixels per side (grid is size x size).
        pixel_size_m: ground sampling distance per pixel, in meters.
        radius_px: boulder radius in pixels.
        height_m: boulder height above the flat base, in meters.
        center: (row, col) pixel center of the boulder; defaults to grid center.

    Returns:
        dict with "elevation" (2D float32 array), "pixel_size_m",
        "source_type" ("synthetic"), and the boulder parameters used
        ("center_px", "radius_px", "height_m") for validation.
    """
    if center is None:
        center = (size // 2, size // 2)
    cy, cx = center

    yy, xx = np.mgrid[0:size, 0:size]
    dist_px = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    norm_dist = dist_px / radius_px

    # Dome shape (hemisphere-like), zero outside the boulder radius.
    dome = height_m * np.sqrt(np.clip(1.0 - norm_dist ** 2, 0.0, None))
    elevation = dome.astype(np.float32)

    return {
        "elevation": elevation,
        "pixel_size_m": pixel_size_m,
        "source_type": "synthetic",
        "center_px": center,
        "radius_px": radius_px,
        "height_m": height_m,
    }
