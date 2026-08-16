import numpy as np

from lunar_hazard_mapper.m4_hazards.gradients import compute_gradients
from lunar_hazard_mapper.m4_hazards.slope import compute_slope, compute_roughness
from lunar_hazard_mapper.m4_hazards.boulder import detect_boulders
from lunar_hazard_mapper.m4_hazards.shadow import detect_shadows
from lunar_hazard_mapper.m4_hazards.confidence import calculate_confidence
from lunar_hazard_mapper.m4_hazards.fusion import fuse_hazards

from tests.m4.fixtures.flat import generate_flat_terrain
from tests.m4.fixtures.slope import generate_slope
from tests.m4.fixtures.boulder import generate_boulder


def _hazard_layers(dem, shadow_mask=None, extra=None):
    slope = compute_slope(compute_gradients(dem))
    roughness = compute_roughness(dem, window=5)
    shadow_mask = shadow_mask if shadow_mask is not None else np.zeros_like(dem["z"], dtype=bool)
    confidence = calculate_confidence({"shadow_mask": shadow_mask})
    layers = {"slope_deg": slope["slope_deg"], "roughness": roughness,
              "confidence": confidence, "shadow_mask": shadow_mask,
              "dx": dem["dx"], "dy": dem["dy"]}
    if extra:
        layers.update(extra)
    return layers


def test_safe_flat_site_passes_binary_mask():
    dem = generate_flat_terrain(shape=(40, 40))
    result = fuse_hazards(_hazard_layers(dem))
    assert not result["binary_mask"].any()
    assert result["continuous_risk"].max() < 0.2


def test_steep_site_rejected():
    dem = generate_slope(shape=(40, 40), angle_deg=25.0)
    result = fuse_hazards(_hazard_layers(dem))
    assert result["binary_mask"].all()


def test_confidence_and_hazard_are_independent_channels():
    """A fully shadowed but geometrically flat/hazard-free region: confidence
    drops, but crater/boulder risk components stay independently zero."""
    dem = generate_flat_terrain(shape=(40, 40))
    shadow_mask = np.ones_like(dem["z"], dtype=bool)
    result = fuse_hazards(_hazard_layers(dem, shadow_mask=shadow_mask))
    assert np.allclose(result["components"]["crater_risk"], 0.0)
    assert np.allclose(result["components"]["boulder_risk"], 0.0)
    assert calculate_confidence({"shadow_mask": shadow_mask}).mean() < 1.0


def test_boulder_detection_on_synthetic_field():
    dem = generate_boulder(shape=(80, 80), n_boulders=4, seed=3)
    boulders = detect_boulders(dem, min_height=0.15)
    assert len(boulders) >= 1
    for b in boulders:
        assert b["height_m"] > 0
        assert 0.0 <= b["confidence"] <= 1.0


def test_shadow_dem_mode_vs_brightness_mode():
    dem = generate_slope(shape=(48, 48), angle_deg=20.0)
    dem_mode = detect_shadows(dem, sun_angle=15.0)
    assert dem_mode.dtype == bool

    brightness = np.random.default_rng(0).uniform(0, 1, size=(48, 48))
    brightness_mode = detect_shadows(brightness, sun_angle=15.0)
    assert brightness_mode.dtype == bool
    assert 0.0 < brightness_mode.mean() < 1.0  # threshold picked SOME but not all pixels


def test_calculate_confidence_requires_at_least_one_input():
    import pytest
    with pytest.raises(ValueError):
        calculate_confidence({})
