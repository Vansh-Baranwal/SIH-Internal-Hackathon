"""Hard feasibility rules for lander-specific site evaluation."""
from __future__ import annotations

from typing import Any, Mapping

from .profile import LanderProfile


def check_hard_constraints(
    site: Mapping[str, Any],
    profile: LanderProfile,
    zone: Mapping[str, Any],
    footprint: Mapping[str, Any],
    *,
    max_unsafe_fraction: float = 0.0,
) -> dict[str, Any]:
    """Return every failed hard constraint for one candidate.

    The caller supplies the precomputed zone and footprint measurements so all
    evaluations use exactly the same M4 grid data and remain explainable.
    """
    if not 0 <= max_unsafe_fraction <= 1:
        raise ValueError("max_unsafe_fraction must be in [0, 1]")
    violations: list[dict[str, Any]] = []
    if not zone.get("in_bounds", False) or not footprint.get("in_bounds", False):
        violations.append(_violation("OUT_OF_BOUNDS", "landing zone or footprint does not fit inside the terrain grid"))
        return {"site_id": site.get("site_id"), "feasible": False, "violations": violations}

    _check_max(violations, "SLOPE_EXCEEDED", zone["max_slope_deg"], profile.max_slope_deg, "landing-zone maximum slope")
    _check_max(violations, "SLOPE_EXCEEDED", footprint["max_slope_deg"], profile.max_slope_deg, "footprint maximum slope")
    _check_max(violations, "UNSAFE_ZONE_FRACTION_EXCEEDED", zone["unsafe_fraction"], max_unsafe_fraction, "unsafe landing-zone fraction")

    if zone["crater_count"] > 0:
        violations.append(_violation("CRATER_IN_ZONE", "crater candidate intersects landing zone", actual=zone["crater_count"], limit=0))
    if footprint.get("crater_intersects_footprint", False):
        violations.append(_violation("FOOTPRINT_HAZARD", "crater intersects lander footprint"))
    if footprint.get("unsafe_pixel_count", 0) > 0:
        violations.append(_violation("FOOTPRINT_HAZARD", "M4 unsafe pixel lies inside lander footprint", actual=footprint["unsafe_pixel_count"], limit=0))

    if profile.min_confidence is not None:
        _check_min(violations, "LOW_CONFIDENCE", zone["min_confidence"], profile.min_confidence, "landing-zone minimum confidence")
        _check_min(violations, "LOW_CONFIDENCE", footprint["min_confidence"], profile.min_confidence, "footprint minimum confidence")
    if profile.max_roughness_m is not None:
        _check_max(violations, "ROUGHNESS_EXCEEDED", zone["max_roughness_m"], profile.max_roughness_m, "landing-zone maximum roughness")
        _check_max(violations, "ROUGHNESS_EXCEEDED", footprint["max_roughness_m"], profile.max_roughness_m, "footprint maximum roughness")
    if profile.min_clearance_m is not None:
        _check_min(violations, "BOULDER_CLEARANCE", footprint["minimum_boulder_clearance_m"], profile.min_clearance_m, "minimum boulder clearance")

    return {"site_id": site.get("site_id"), "feasible": not violations, "violations": violations}


def _check_max(violations: list[dict[str, Any]], code: str, actual: float, limit: float, label: str) -> None:
    if actual > limit:
        violations.append(_violation(code, f"{label} exceeds limit", actual=actual, limit=limit))


def _check_min(violations: list[dict[str, Any]], code: str, actual: float, limit: float, label: str) -> None:
    if actual < limit:
        violations.append(_violation(code, f"{label} is below limit", actual=actual, limit=limit))


def _violation(code: str, message: str, *, actual: float | int | str | None = None, limit: float | int | str | None = None) -> dict[str, Any]:
    return {"code": code, "actual": actual, "limit": limit, "message": message}
