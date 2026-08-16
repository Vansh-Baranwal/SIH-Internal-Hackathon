"""src/lunar_hazard_mapper/m4_hazards/fusion.py"""
from __future__ import annotations
import numpy as np


def fuse_hazards(hazard_layers: dict) -> dict:
    """Two required outputs per M4-P / handbook 5.10:
        H(x,y) = S OR C_r OR B OR U    -- strict binary operational mask
        R = w_s*R_s + w_c*R_c + w_b*R_b + w_u*R_u + w_r*R_rough  -- continuous risk
    Confidence and hazard probability stay separate channels throughout
    (M4-O / critical warning is architectural, not just documentation):
    confidence only ever enters as one weighted term in R and as one
    independent trigger in the binary OR -- it is never derived from hazard
    or vice versa.

    Args:
        hazard_layers: {
            "slope_deg": ndarray,
            "roughness": ndarray,
            "confidence": ndarray in [0,1],
            "shadow_mask": bool ndarray,
            "dx": float, "dy": float,
            # craters/boulders as EITHER already-rasterized arrays...
            "crater_raster": ndarray (optional),
            "boulder_raster": ndarray (optional),
            # ...OR raw candidate lists from crater.py/boulder.py, which
            # get splatted onto a raster here using each candidate's own
            # radius (Gaussian footprint):
            "craters": list[dict] (optional, needs center_row/col + diameter_m or radius_m),
            "boulders": list[dict] (optional, needs center_row/col + hazard_radius_m or radius_m),
            "slope_limit_deg": float, default 10.0 (SIH example threshold),
            "weights": dict, default {"slope":.30,"crater":.25,"boulder":.25,"uncertainty":.10,"roughness":.10},
            "binary_confidence_floor": float, default 0.35,
        }

    Returns:
        {"binary_mask": bool ndarray, "continuous_risk": ndarray in [0,1],
         "components": {"slope_risk","crater_risk","boulder_risk","roughness_risk","uncertainty_risk"}}
    """
    slope_deg = hazard_layers["slope_deg"]
    roughness = hazard_layers["roughness"]
    confidence = hazard_layers["confidence"]
    shadow_mask = hazard_layers["shadow_mask"]
    shape = slope_deg.shape
    dx = hazard_layers.get("dx", 1.0)

    slope_limit = hazard_layers.get("slope_limit_deg", 10.0)
    w = hazard_layers.get("weights", {
        "slope": 0.30, "crater": 0.25, "boulder": 0.25, "uncertainty": 0.10, "roughness": 0.10})
    conf_floor = hazard_layers.get("binary_confidence_floor", 0.35)

    crater_raster = hazard_layers.get("crater_raster")
    if crater_raster is None:
        crater_raster = _rasterize_points(shape, hazard_layers.get("craters", []), dx,
                                           radius_key="diameter_m", radius_scale=0.5)
    boulder_raster = hazard_layers.get("boulder_raster")
    if boulder_raster is None:
        boulder_raster = _rasterize_points(shape, hazard_layers.get("boulders", []), dx,
                                            radius_key="hazard_radius_m", radius_scale=1.0)

    slope_risk = _normalize(slope_deg, 0.0, max(slope_limit * 2, float(slope_deg.max()) + 1e-9))
    roughness_risk = _normalize(roughness)
    crater_risk = _normalize(crater_raster) if crater_raster.max() > 0 else crater_raster
    boulder_risk = _normalize(boulder_raster) if boulder_raster.max() > 0 else boulder_raster
    uncertainty_risk = 1.0 - confidence

    continuous_risk = np.clip(
        w["slope"] * slope_risk + w["crater"] * crater_risk + w["boulder"] * boulder_risk +
        w["uncertainty"] * uncertainty_risk + w["roughness"] * roughness_risk, 0.0, 1.0)

    binary_mask = (
        (slope_deg > slope_limit) | (crater_risk > 0.5) | (boulder_risk > 0.5) |
        (confidence < conf_floor)
    )

    return {
        "binary_mask": binary_mask,
        "continuous_risk": continuous_risk,
        "components": {
            "slope_risk": slope_risk, "crater_risk": crater_risk,
            "boulder_risk": boulder_risk, "roughness_risk": roughness_risk,
            "uncertainty_risk": uncertainty_risk, "shadow_mask": shadow_mask,
        },
    }


def _rasterize_points(shape, points: list[dict], dx: float, radius_key: str, radius_scale: float) -> np.ndarray:
    h, w = shape
    if not points:
        return np.zeros(shape, dtype=np.float64)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    raster = np.zeros(shape, dtype=np.float64)
    for p in points:
        cy, cx = p["center_row"], p["center_col"]
        val = p.get("confidence", 1.0)
        radius_m = p.get(radius_key, p.get("radius_m", dx)) * radius_scale
        radius_px = max(radius_m / dx, 1.0)
        r2 = (xx - cx) ** 2 + (yy - cy) ** 2
        raster = np.maximum(raster, val * np.exp(-r2 / (2 * radius_px ** 2)))
    return raster


def _normalize(x: np.ndarray, x_min: float | None = None, x_max: float | None = None) -> np.ndarray:
    x_min = float(np.min(x)) if x_min is None else x_min
    x_max = float(np.max(x)) if x_max is None else x_max
    if x_max - x_min < 1e-9:
        return np.zeros_like(x, dtype=np.float64)
    return np.clip((x - x_min) / (x_max - x_min), 0.0, 1.0)
