"""Transparent soft ranking for feasible landing sites."""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .profile import LanderProfile


DEFAULT_WEIGHTS = {"risk": 0.45, "target_distance": 0.25, "delta_v": 0.15, "terrain_quality": 0.15}


def score_site(
    site: Mapping[str, Any],
    profile: LanderProfile,
    zone: Mapping[str, Any],
    footprint: Mapping[str, Any],
    *,
    target_xy_m: tuple[float, float] | None = None,
    delta_v_mps: float | None = None,
    distance_scale_m: float = 1_000.0,
    delta_v_scale_mps: float = 1_000.0,
    weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Score a feasible site from 0 to 1, retaining all decision factors.

    Higher scores are better. A missing target or delta-v estimate removes its
    weight and normalises the remaining available weights, rather than
    pretending the absent value is favourable.
    """
    if distance_scale_m <= 0 or delta_v_scale_mps <= 0:
        raise ValueError("distance and delta-v scales must be positive")
    if not zone.get("in_bounds") or not footprint.get("in_bounds"):
        raise ValueError("cannot score an out-of-bounds site")
    applied_weights = _normalise_weights(weights, target_xy_m is not None, delta_v_mps is not None)
    risk = 1.0 - np.clip(0.6 * float(zone["mean_risk"]) + 0.4 * float(footprint["max_risk"]), 0.0, 1.0)
    slope_quality = np.clip(1.0 - float(footprint["max_slope_deg"]) / profile.max_slope_deg, 0.0, 1.0) if profile.max_slope_deg else 0.0
    terrain_quality = 0.5 * slope_quality + 0.5 * np.clip(float(footprint["min_confidence"]), 0.0, 1.0)
    components: dict[str, float | None] = {"risk": float(risk), "terrain_quality": float(terrain_quality)}
    if target_xy_m is None:
        components["target_distance"] = None
    else:
        distance = np.hypot(float(site["x_m"]) - target_xy_m[0], float(site["y_m"]) - target_xy_m[1])
        components["target_distance"] = float(1.0 - min(distance / distance_scale_m, 1.0))
    components["delta_v"] = None if delta_v_mps is None else float(1.0 - min(max(delta_v_mps, 0.0) / delta_v_scale_mps, 1.0))
    score = sum(applied_weights[name] * float(components[name]) for name in applied_weights)
    return {"site_id": site.get("site_id"), "score": float(score), "score_components": components, "weights": applied_weights}


def _normalise_weights(weights: Mapping[str, float] | None, has_target: bool, has_delta_v: bool) -> dict[str, float]:
    supplied = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(supplied) != set(DEFAULT_WEIGHTS) or any(value < 0 for value in supplied.values()):
        raise ValueError(f"weights must contain non-negative values for {sorted(DEFAULT_WEIGHTS)}")
    available = {"risk", "terrain_quality"}
    if has_target:
        available.add("target_distance")
    if has_delta_v:
        available.add("delta_v")
    total = sum(supplied[name] for name in available)
    if total <= 0:
        raise ValueError("at least one available score weight must be positive")
    return {name: supplied[name] / total for name in sorted(available)}
