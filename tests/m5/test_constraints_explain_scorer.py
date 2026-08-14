import pytest

from src.lunar_hazard_mapper.m5_lander.constraints import check_hard_constraints
from src.lunar_hazard_mapper.m5_lander.explain import generate_rejection_reason
from src.lunar_hazard_mapper.m5_lander.profile import LanderProfile
from src.lunar_hazard_mapper.m5_lander.scorer import score_site


SITE = {"site_id": "r20_c20", "row": 20, "col": 20, "x_m": 20.0, "y_m": 20.0}
ZONE = {"in_bounds": True, "max_slope_deg": 6.0, "unsafe_fraction": 0.0, "crater_count": 0,
        "min_confidence": 0.9, "max_roughness_m": 0.1, "mean_risk": 0.2}
FOOTPRINT = {"in_bounds": True, "max_slope_deg": 6.0, "unsafe_pixel_count": 0,
             "crater_intersects_footprint": False, "min_confidence": 0.9,
             "max_roughness_m": 0.1, "minimum_boulder_clearance_m": float("inf"), "max_risk": 0.1}


def test_constraints_return_all_slope_violations_and_explanation():
    result = check_hard_constraints(SITE, LanderProfile("B", 1, 5, footprint_radius_m=2), ZONE, FOOTPRINT)
    assert result["feasible"] is False
    assert [item["code"] for item in result["violations"]] == ["SLOPE_EXCEEDED", "SLOPE_EXCEEDED"]
    explanation = generate_rejection_reason(SITE, result["violations"])
    assert explanation["reason_codes"] == ["SLOPE_EXCEEDED"]
    assert explanation["row"] == 20


def test_constraints_apply_optional_confidence_and_roughness_limits():
    profile = LanderProfile("Strict", 1, 10, footprint_radius_m=2, min_confidence=0.95, max_roughness_m=0.05)
    result = check_hard_constraints(SITE, profile, ZONE, FOOTPRINT)
    assert {item["code"] for item in result["violations"]} == {"LOW_CONFIDENCE", "ROUGHNESS_EXCEEDED"}


def test_score_is_transparent_and_prefers_nearer_lower_risk_site():
    profile = LanderProfile("A", 1, 10, footprint_radius_m=2)
    better = score_site(SITE, profile, {**ZONE, "max_slope_deg": 4, "mean_risk": 0.1}, {**FOOTPRINT, "max_slope_deg": 4, "max_risk": 0.1}, target_xy_m=(20, 20))
    worse = score_site({**SITE, "site_id": "far", "x_m": 1020.0}, profile, ZONE, FOOTPRINT, target_xy_m=(20, 20))
    assert better["score"] > worse["score"]
    assert better["score_components"]["delta_v"] is None
    assert "delta_v" not in better["weights"]


def test_explanation_requires_violation():
    with pytest.raises(ValueError, match="at least one"):
        generate_rejection_reason(SITE, [])
