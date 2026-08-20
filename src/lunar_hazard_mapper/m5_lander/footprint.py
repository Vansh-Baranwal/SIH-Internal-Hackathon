"""Circular lander-footprint evaluation on the M4 hazard grid."""
from __future__ import annotations

from math import ceil
from typing import Any, Mapping

import numpy as np

from .landing_zone import _extract_rasters, _site_index
from .profile import LanderProfile


def evaluate_footprint(
    site: Mapping[str, Any],
    profile: LanderProfile,
    m4_to_m5: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate every pixel inside a configured circular lander footprint.

    The profile must declare ``footprint_radius_m``. Current project YAML
    files intentionally omit it, so callers must obtain an agreed radius
    before claiming a physical-footprint evaluation is complete.
    """
    if profile.footprint_radius_m is None:
        raise ValueError(f"{profile.name} needs footprint_radius_m for footprint evaluation")
    terrain, hazards = _extract_rasters(m4_to_m5)
    row, col = _site_index(site)
    z, dx, dy = terrain["z"], terrain["dx"], terrain["dy"]
    radius = profile.footprint_radius_m
    row_radius, col_radius = ceil(radius / dy), ceil(radius / dx)
    row_start, row_end = row - row_radius, row + row_radius + 1
    col_start, col_end = col - col_radius, col + col_radius + 1
    if row_start < 0 or col_start < 0 or row_end > z.shape[0] or col_end > z.shape[1]:
        return {"site_id": site.get("site_id"), "in_bounds": False, "safe": False,
                "reason": "OUT_OF_BOUNDS", "checked_pixel_count": 0}

    row_offsets = np.arange(row_start, row_end) - row
    col_offsets = np.arange(col_start, col_end) - col
    yy, xx = np.meshgrid(row_offsets * dy, col_offsets * dx, indexing="ij")
    mask = (xx ** 2 + yy ** 2) <= radius ** 2 + 1e-12
    window = np.s_[row_start:row_end, col_start:col_end]
    selected = {name: values[window][mask] for name, values in hazards.items()}
    boulder_clearance = _minimum_boulder_clearance(site, radius, dx, dy, m4_to_m5.get("boulders", []))
    crater_in_footprint = _crater_intersects_footprint(site, radius, dx, dy, m4_to_m5.get("craters", []))

    passes = {
        "slope": bool(np.max(selected["slope_deg"]) <= profile.max_slope_deg),
        "hazards": bool(not np.any(selected["binary_mask"]) and not crater_in_footprint),
        "confidence": profile.min_confidence is None or bool(np.min(selected["confidence"]) >= profile.min_confidence),
        "roughness": profile.max_roughness_m is None or bool(np.max(selected["roughness"]) <= profile.max_roughness_m),
        "boulder_clearance": profile.min_clearance_m is None or bool(boulder_clearance >= profile.min_clearance_m),
    }
    return {
        "site_id": site.get("site_id"), "in_bounds": True,
        "safe": all(passes.values()), "passes": passes,
        "checked_pixel_count": int(np.count_nonzero(mask)),
        "max_slope_deg": float(np.max(selected["slope_deg"])),
        "max_risk": float(np.max(selected["continuous_risk"])),
        "mean_risk": float(np.mean(selected["continuous_risk"])),
        "min_confidence": float(np.min(selected["confidence"])),
        "max_roughness_m": float(np.max(selected["roughness"])),
        "unsafe_pixel_count": int(np.count_nonzero(selected["binary_mask"])),
        "minimum_boulder_clearance_m": boulder_clearance,
        "crater_intersects_footprint": crater_in_footprint,
    }


def _minimum_boulder_clearance(site: Mapping[str, Any], footprint_radius_m: float, dx: float, dy: float, boulders: list[Mapping[str, Any]]) -> float:
    row, col = _site_index(site)
    clearances = []
    for boulder in boulders:
        distance = np.hypot((float(boulder["center_row"]) - row) * dy, (float(boulder["center_col"]) - col) * dx)
        clearances.append(distance - footprint_radius_m - float(boulder.get("hazard_radius_m", boulder.get("radius_m", 0.0))))
    return float(min(clearances)) if clearances else 9999.0


def _crater_intersects_footprint(site: Mapping[str, Any], footprint_radius_m: float, dx: float, dy: float, craters: list[Mapping[str, Any]]) -> bool:
    row, col = _site_index(site)
    for crater in craters:
        distance = np.hypot((float(crater["center_row"]) - row) * dy, (float(crater["center_col"]) - col) * dx)
        if distance <= footprint_radius_m + float(crater.get("diameter_m", 0.0)) / 2:
            return True
    return False
