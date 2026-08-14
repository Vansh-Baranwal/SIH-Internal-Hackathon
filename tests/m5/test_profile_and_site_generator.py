import pytest

from src.lunar_hazard_mapper.m5_lander.profile import LanderProfile, load_lander_profile
from src.lunar_hazard_mapper.m5_lander.site_generator import generate_candidate_sites
from synthetic.terrain.flat import generate_flat_terrain


def test_load_existing_lander_profile():
    profile = load_lander_profile("configs/landers/lander_B.yaml")
    assert profile.name == "Lander B"
    assert profile.max_slope_deg == 5
    assert profile.landing_zone_size_m == 24.0
    assert profile.footprint_radius_m is None


def test_profile_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="min_confidence"):
        LanderProfile(name="Test", mass_kg=1, max_slope_deg=5, min_confidence=1.1)


def test_candidates_stay_inside_24m_zone_and_use_origin():
    terrain = generate_flat_terrain(shape=(50, 50), dx=1.0, dy=1.0)
    terrain["origin"] = {"x_m": 100.0, "y_m": 200.0}
    candidates = generate_candidate_sites(terrain, landing_zone_size_m=24.0, spacing_m=24.0)

    assert candidates
    assert all(12 <= site["row"] <= 37 for site in candidates)
    assert all(12 <= site["col"] <= 37 for site in candidates)
    assert candidates[0]["x_m"] == 112.0
    assert candidates[0]["y_m"] == 212.0


def test_candidates_accept_complete_m4_payload_and_return_empty_when_zone_cannot_fit():
    terrain = generate_flat_terrain(shape=(20, 20), dx=1.0, dy=1.0)
    assert generate_candidate_sites({"terrain": terrain}) == []
