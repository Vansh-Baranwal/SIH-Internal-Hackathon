"""src/lunar_hazard_mapper/m4_hazards/crater.py"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from skimage import morphology, measure

from .gradients import compute_gradients
from .slope import compute_slope


def detect_craters(dem: dict, depression_min_depth: float = 1.0,
                    min_area_px: int = 9, max_area_px: int = 20000) -> list[dict]:
    """Morphology + local-depression baseline (handbook 5.7, spec M4-H):
    deliberately not a deep-learning detector -- the spec requires this
    transparent baseline before any YOLO/SAM upgrade (M4-I, Method Ladder §12).

    Pipeline: grayscale reconstruction-by-erosion fills basins -> depression
    = filled - z -> threshold -> connected components -> per-region depth
    (rim - floor), diameter (max pairwise distance on the region boundary,
    handbook 5.7 D=max_{p,q}||p-q||), rim slope, confidence.

    Args:
        dem: {"z": ndarray, "dx": float, "dy": float}

    Returns:
        list of dicts, one per candidate crater:
        {id, center_row, center_col, diameter_px, diameter_m, depth_m,
         rim_elevation_m, floor_elevation_m, rim_slope_deg, confidence}
    """
    z = np.asarray(dem["z"], dtype=np.float64)
    dx, dy = float(dem["dx"]), float(dem["dy"])
    slope_deg = compute_slope(compute_gradients(dem))["slope_deg"]

    marker = np.full_like(z, z.max())
    marker[0, :], marker[-1, :] = z[0, :], z[-1, :]
    marker[:, 0], marker[:, -1] = z[:, 0], z[:, -1]
    filled = morphology.reconstruction(marker, z, method="erosion")
    depression = filled - z

    mask = depression > depression_min_depth
    mask = ndimage.binary_closing(mask, structure=np.ones((3, 3)))
    labeled, _ = ndimage.label(mask)

    candidates = []
    for region in measure.regionprops(labeled, intensity_image=z):
        if region.area < min_area_px or region.area > max_area_px:
            continue
        rows, cols = np.where(labeled == region.label)
        floor_elev = float(z[rows, cols].min())

        ring = ndimage.binary_dilation(labeled == region.label, iterations=3) & (labeled != region.label)
        rim_elev = float(z[ring].max()) if ring.any() else float(z[rows, cols].max())
        depth = rim_elev - floor_elev
        if depth < depression_min_depth:
            continue

        coords = np.stack([rows, cols], axis=1).astype(np.float64)
        if len(coords) > 400:
            idx = np.random.default_rng(0).choice(len(coords), 400, replace=False)
            coords = coords[idx]
        diam_m = _max_pairwise_distance(coords, dx, dy)
        diam_px = diam_m / max(dx, 1e-12)

        rim_slope = float(np.mean(slope_deg[rows, cols])) if len(rows) else 0.0
        area_conf = min(1.0, region.area / min_area_px / 4.0)
        depth_conf = min(1.0, depth / (3 * depression_min_depth))
        confidence = float(np.clip(0.5 * area_conf + 0.5 * depth_conf, 0.0, 1.0))

        candidates.append({
            "id": len(candidates),
            "center_row": float(region.centroid[0]), "center_col": float(region.centroid[1]),
            "diameter_px": diam_px, "diameter_m": diam_m,
            "depth_m": depth, "rim_elevation_m": rim_elev, "floor_elevation_m": floor_elev,
            "rim_slope_deg": rim_slope, "confidence": confidence,
        })
    return candidates


def _max_pairwise_distance(coords: np.ndarray, dx: float, dy: float) -> float:
    if len(coords) < 2:
        return 0.0
    scaled = coords * np.array([dy, dx])
    try:
        from scipy.spatial import ConvexHull
        pts = scaled[ConvexHull(scaled).vertices]
    except Exception:
        pts = scaled
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    return float(d.max())
