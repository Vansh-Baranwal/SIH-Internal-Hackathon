"""Candidate landing-site generation on an M4/M5 terrain grid."""
from __future__ import annotations

from math import ceil
from typing import Any, Mapping

import numpy as np


def generate_candidate_sites(
    terrain: Mapping[str, Any],
    *,
    landing_zone_size_m: float = 24.0,
    spacing_m: float | None = None,
) -> list[dict[str, int | float | str]]:
    """Generate deterministic candidate centres with a complete landing zone.

    ``terrain`` may be either M4's ``m4_to_m5["terrain"]`` dictionary or
    the complete M4-to-M5 payload. Candidates are deliberately generated from
    geometry only; hazard filtering belongs to the evaluator, where it can be
    applied separately for each lander profile.
    """
    if landing_zone_size_m <= 0:
        raise ValueError("landing_zone_size_m must be positive")
    terrain_data = terrain.get("terrain", terrain)
    if not isinstance(terrain_data, Mapping):
        raise ValueError("terrain must be a terrain mapping or M4-to-M5 payload")

    z = np.asarray(terrain_data["z"])
    if z.ndim != 2:
        raise ValueError("terrain['z'] must be a two-dimensional grid")
    dx, dy = float(terrain_data["dx"]), float(terrain_data["dy"])
    if dx <= 0 or dy <= 0:
        raise ValueError("terrain dx and dy must be positive")

    sample_spacing_m = landing_zone_size_m if spacing_m is None else float(spacing_m)
    if sample_spacing_m <= 0:
        raise ValueError("spacing_m must be positive")

    row_margin = ceil((landing_zone_size_m / 2) / dy)
    col_margin = ceil((landing_zone_size_m / 2) / dx)
    height, width = z.shape
    row_start, row_end = row_margin, height - row_margin - 1
    col_start, col_end = col_margin, width - col_margin - 1
    if row_start > row_end or col_start > col_end:
        return []

    rows = _sample_indices(row_start, row_end, ceil(sample_spacing_m / dy))
    cols = _sample_indices(col_start, col_end, ceil(sample_spacing_m / dx))
    origin = terrain_data.get("origin", {})
    origin_x = float(origin.get("x_m", 0.0))
    origin_y = float(origin.get("y_m", 0.0))

    candidates: list[dict[str, int | float | str]] = []
    for row in rows:
        for col in cols:
            candidates.append({
                "site_id": f"r{row}_c{col}",
                "row": row,
                "col": col,
                "x_m": origin_x + col * dx,
                "y_m": origin_y + row * dy,
                "elevation_m": float(z[row, col]),
            })
    return candidates


def _sample_indices(start: int, end: int, stride: int) -> list[int]:
    indices = list(range(start, end + 1, max(1, stride)))
    if indices[-1] != end:
        indices.append(end)
    return indices
