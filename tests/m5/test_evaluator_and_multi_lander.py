import numpy as np

from src.lunar_hazard_mapper.m5_lander.evaluator import evaluate_sites
from src.lunar_hazard_mapper.m5_lander.multi_lander import compare_landers
from src.lunar_hazard_mapper.m5_lander.profile import LanderProfile


def _payload():
    shape = (60, 60)
    zeros = np.zeros(shape)
    return {
        "terrain": {"z": np.full(shape, 1000.0), "dx": 1.0, "dy": 1.0},
        "hazards": {"slope_deg": zeros.copy(), "binary_mask": np.zeros(shape, dtype=bool),
                    "continuous_risk": zeros.copy(), "confidence": np.ones(shape),
                    "roughness": zeros.copy(), "crater_risk": zeros.copy(),
                    "boulder_risk": zeros.copy()},
        "craters": [], "boulders": [],
    }


def test_evaluator_returns_ranked_accepted_and_explained_rejected_sites():
    payload = _payload()
    payload["hazards"]["slope_deg"][45, 45] = 12.0
    sites = [{"site_id": "safe", "row": 20, "col": 20, "x_m": 20.0, "y_m": 20.0},
             {"site_id": "steep", "row": 45, "col": 45, "x_m": 45.0, "y_m": 45.0}]
    result = evaluate_sites(sites, LanderProfile("A", 1, 10, footprint_radius_m=2), payload)
    assert [site["site_id"] for site in result["recommended_sites"]] == ["safe"]
    assert result["recommended_sites"][0]["rank"] == 1
    assert "SLOPE_EXCEEDED" in result["rejected_sites"][0]["reason_codes"]


def test_multi_lander_identifies_profile_specific_slope_feasibility():
    payload = _payload()
    payload["hazards"]["slope_deg"][45, 45] = 7.0  # M4 binary mask stays false.
    sites = [{"site_id": "flat", "row": 20, "col": 20, "x_m": 20.0, "y_m": 20.0},
             {"site_id": "seven_deg", "row": 45, "col": 45, "x_m": 45.0, "y_m": 45.0}]
    comparison = compare_landers(payload, [
        LanderProfile("A", 1, 10, footprint_radius_m=2),
        LanderProfile("B", 1, 5, footprint_radius_m=2),
    ], sites=sites)
    assert comparison["shared_safe_sites"] == ["flat"]
    assert comparison["lander_specific_safe_sites"]["A"] == ["seven_deg"]
    assert comparison["rejected_site_reasons"]["B"]["seven_deg"] == ["SLOPE_EXCEEDED"]
