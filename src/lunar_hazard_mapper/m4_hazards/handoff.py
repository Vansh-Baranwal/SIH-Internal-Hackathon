"""M4 -> M5 handoff assembly helpers.

This module builds the raster-and-candidates payload expected by Member 5
from already computed M4 outputs (dem, slope, fusion, detections, etc.).
"""
from __future__ import annotations

import numpy as np


def build_m4_to_m5(
    *,
    dem: dict,
    slope: dict,
    roughness: np.ndarray,
    confidence: np.ndarray,
    shadow_mask: np.ndarray,
    fused: dict,
    craters: list[dict],
    boulders: list[dict],
) -> dict:
    """Build the M4 -> M5 payload according to the integration contract.

    Required shape rule: every raster in hazards must share the DEM grid shape.
    """
    z = np.asarray(dem["z"], dtype=np.float64)
    slope_deg = np.asarray(slope["slope_deg"], dtype=np.float64)
    roughness_arr = np.asarray(roughness, dtype=np.float64)
    confidence_arr = np.asarray(confidence, dtype=np.float64)
    shadow_arr = np.asarray(shadow_mask, dtype=bool)
    binary_mask = np.asarray(fused["binary_mask"], dtype=bool)
    continuous_risk = np.asarray(fused["continuous_risk"], dtype=np.float64)

    shape = z.shape
    for name, arr in (
        ("slope_deg", slope_deg),
        ("roughness", roughness_arr),
        ("confidence", confidence_arr),
        ("shadow_mask", shadow_arr),
        ("binary_mask", binary_mask),
        ("continuous_risk", continuous_risk),
    ):
        if arr.shape != shape:
            raise ValueError(f"{name} shape {arr.shape} does not match DEM shape {shape}")

    components = fused.get("components", {})
    crater_risk = np.asarray(components.get("crater_risk", np.zeros(shape)), dtype=np.float64)
    boulder_risk = np.asarray(components.get("boulder_risk", np.zeros(shape)), dtype=np.float64)
    if crater_risk.shape != shape or boulder_risk.shape != shape:
        raise ValueError("crater_risk/boulder_risk shape must match DEM shape")

    terrain = {
        "z": z,
        "dx": float(dem["dx"]),
        "dy": float(dem["dy"]),
    }

    origin = dem.get("origin")
    if isinstance(origin, dict) and "x_m" in origin and "y_m" in origin:
        terrain["origin"] = {
            "x_m": float(origin["x_m"]),
            "y_m": float(origin["y_m"]),
        }

    hazards = {
        "slope_deg": slope_deg,
        "binary_mask": binary_mask,
        "continuous_risk": np.clip(continuous_risk, 0.0, 1.0),
        "confidence": np.clip(confidence_arr, 0.0, 1.0),
        "roughness": roughness_arr,
        "crater_risk": np.clip(crater_risk, 0.0, 1.0),
        "boulder_risk": np.clip(boulder_risk, 0.0, 1.0),
        "shadow_mask": shadow_arr,
    }

    return {
        "terrain": terrain,
        "hazards": hazards,
        "craters": _normalize_craters(craters),
        "boulders": _normalize_boulders(boulders),
    }


def _normalize_craters(craters: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for i, c in enumerate(craters or []):
        normalized.append({
            "id": int(c.get("id", i)),
            "center_row": float(c["center_row"]),
            "center_col": float(c["center_col"]),
            "diameter_m": float(c.get("diameter_m", 0.0)),
            "depth_m": float(c.get("depth_m", 0.0)),
            "rim_slope_deg": float(c.get("rim_slope_deg", 0.0)),
            "confidence": float(np.clip(c.get("confidence", 0.0), 0.0, 1.0)),
        })
    return normalized


def _normalize_boulders(boulders: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for i, b in enumerate(boulders or []):
        normalized.append({
            "id": int(b.get("id", i)),
            "center_row": float(b["center_row"]),
            "center_col": float(b["center_col"]),
            "height_m": float(b.get("height_m", 0.0)),
            "radius_m": float(b.get("radius_m", 0.0)),
            "hazard_radius_m": float(b.get("hazard_radius_m", 0.0)),
            "confidence": float(np.clip(b.get("confidence", 0.0), 0.0, 1.0)),
        })
    return normalized
