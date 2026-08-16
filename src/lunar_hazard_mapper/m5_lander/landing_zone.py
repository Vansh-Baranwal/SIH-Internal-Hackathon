"""Landing-zone statistics for Member 5 site evaluation."""
from __future__ import annotations

from math import ceil
from typing import Any, Mapping

import numpy as np


def analyze_landing_zone(
    site: Mapping[str, Any],
    m4_to_m5: Mapping[str, Any],
    *,
    radius_m: float = 12.0,
) -> dict[str, Any]:
    """Summarise the rectangular landing zone centred on ``site``.

    A 24 × 24 m zone uses the default 12 m radius. The function returns an
    out-of-bounds result instead of clipping windows: a clipped zone is not a
    valid complete landing area.
    """
    if radius_m <= 0:
        raise ValueError("radius_m must be positive")
    terrain, hazards = _extract_rasters(m4_to_m5)
    z = terrain["z"]
    row, col = _site_index(site)
    dx, dy = terrain["dx"], terrain["dy"]

    height_px = ceil((2 * radius_m) / dy)
    width_px = ceil((2 * radius_m) / dx)
    row_start, row_end = row - height_px // 2, row - height_px // 2 + height_px
    col_start, col_end = col - width_px // 2, col - width_px // 2 + width_px
    if row_start < 0 or col_start < 0 or row_end > z.shape[0] or col_end > z.shape[1]:
        return {
            "site_id": site.get("site_id"), "in_bounds": False,
            "reason": "OUT_OF_BOUNDS", "row_bounds": (row_start, row_end),
            "col_bounds": (col_start, col_end),
        }

    window = np.s_[row_start:row_end, col_start:col_end]
    crater_count = _objects_in_window(m4_to_m5.get("craters", []), row_start, row_end, col_start, col_end)
    boulder_count = _objects_in_window(m4_to_m5.get("boulders", []), row_start, row_end, col_start, col_end)
    return {
        "site_id": site.get("site_id"), "in_bounds": True,
        "row_bounds": (row_start, row_end), "col_bounds": (col_start, col_end),
        "size_m": {"x": width_px * dx, "y": height_px * dy},
        "pixel_count": height_px * width_px,
        "max_slope_deg": float(np.max(hazards["slope_deg"][window])),
        "mean_slope_deg": float(np.mean(hazards["slope_deg"][window])),
        "max_risk": float(np.max(hazards["continuous_risk"][window])),
        "mean_risk": float(np.mean(hazards["continuous_risk"][window])),
        "unsafe_fraction": float(np.mean(hazards["binary_mask"][window])),
        "min_confidence": float(np.min(hazards["confidence"][window])),
        "max_roughness_m": float(np.max(hazards["roughness"][window])),
        "mean_roughness_m": float(np.mean(hazards["roughness"][window])),
        "max_crater_risk": float(np.max(hazards["crater_risk"][window])),
        "max_boulder_risk": float(np.max(hazards["boulder_risk"][window])),
        "crater_count": crater_count,
        "boulder_count": boulder_count,
    }


def _extract_rasters(m4_to_m5: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    try:
        terrain_raw, hazards_raw = m4_to_m5["terrain"], m4_to_m5["hazards"]
        terrain = {"z": np.asarray(terrain_raw["z"]), "dx": float(terrain_raw["dx"]), "dy": float(terrain_raw["dy"])}
        hazards = {name: np.asarray(hazards_raw[name]) for name in (
            "slope_deg", "binary_mask", "continuous_risk", "confidence", "roughness",
            "crater_risk", "boulder_risk",
        )}
    except (KeyError, TypeError) as exc:
        raise ValueError("m4_to_m5 must contain terrain and required hazard rasters") from exc
    if terrain["z"].ndim != 2 or terrain["dx"] <= 0 or terrain["dy"] <= 0:
        raise ValueError("terrain must contain a 2D z grid and positive dx/dy")
    if any(array.shape != terrain["z"].shape for array in hazards.values()):
        raise ValueError("all M4 hazard rasters must match the terrain grid shape")
    return terrain, hazards


def _site_index(site: Mapping[str, Any]) -> tuple[int, int]:
    try:
        return int(site["row"]), int(site["col"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("site must provide integer row and col") from exc


def _objects_in_window(objects: list[Mapping[str, Any]], row_start: int, row_end: int, col_start: int, col_end: int) -> int:
    return sum(
        row_start <= float(item["center_row"]) < row_end and col_start <= float(item["center_col"]) < col_end
        for item in objects
    )
