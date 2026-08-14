import numpy as np
import pytest

from src.lunar_hazard_mapper.m5_lander.footprint import evaluate_footprint
from src.lunar_hazard_mapper.m5_lander.landing_zone import analyze_landing_zone
from src.lunar_hazard_mapper.m5_lander.profile import LanderProfile


def _payload(shape=(40, 40)):
    zeros = np.zeros(shape)
    return {
        "terrain": {"z": np.full(shape, 1000.0), "dx": 1.0, "dy": 1.0},
        "hazards": {"slope_deg": zeros.copy(), "binary_mask": np.zeros(shape, dtype=bool),
                    "continuous_risk": zeros.copy(), "confidence": np.ones(shape),
                    "roughness": zeros.copy(), "crater_risk": zeros.copy(),
                    "boulder_risk": zeros.copy()},
        "craters": [], "boulders": [],
    }


def test_landing_zone_returns_statistics_and_detected_objects():
    payload = _payload()
    payload["hazards"]["slope_deg"][10:34, 10:34] = 4.0
    payload["hazards"]["continuous_risk"][20, 20] = 0.8
    payload["craters"] = [{"center_row": 20, "center_col": 20}]
    result = analyze_landing_zone({"site_id": "centre", "row": 22, "col": 22}, payload)
    assert result["in_bounds"] is True
    assert result["pixel_count"] == 24 * 24
    assert result["max_slope_deg"] == 4.0
    assert result["max_risk"] == 0.8
    assert result["crater_count"] == 1


def test_landing_zone_rejects_incomplete_border_window():
    assert analyze_landing_zone({"row": 5, "col": 20}, _payload())["reason"] == "OUT_OF_BOUNDS"


def test_footprint_checks_all_pixels_and_profile_limits():
    payload = _payload()
    payload["hazards"]["slope_deg"][20, 22] = 6.0  # inside a 3 m footprint, not at its centre
    profile = LanderProfile(name="Strict", mass_kg=1, max_slope_deg=5, footprint_radius_m=3)
    result = evaluate_footprint({"row": 20, "col": 20}, profile, payload)
    assert result["checked_pixel_count"] > 1
    assert result["passes"]["slope"] is False
    assert result["safe"] is False


def test_footprint_requires_an_agreed_radius():
    with pytest.raises(ValueError, match="footprint_radius_m"):
        evaluate_footprint({"row": 20, "col": 20}, LanderProfile("No radius", 1, 5), _payload())
