"""
tests/m4/test_terrain_math.py

Implements the M4 rows of the workflow's testing matrix (§11): flat->0deg,
5deg/10deg plane recovery, ridge/bowl Hessian sign checks, crater
depth/diameter recovery.
"""
import numpy as np
import pytest

from lunar_hazard_mapper.m4_hazards.gradients import compute_gradients
from lunar_hazard_mapper.m4_hazards.slope import compute_slope, compute_roughness
from lunar_hazard_mapper.m4_hazards.hessian import compute_hessian
from lunar_hazard_mapper.m4_hazards.curvature import compute_curvature
from lunar_hazard_mapper.m4_hazards.eigenfeatures import compute_eigenfeatures
from lunar_hazard_mapper.m4_hazards.crater import detect_craters

from synthetic.terrain.flat import generate_flat_terrain
from synthetic.terrain.slope import generate_slope, generate_ridge, generate_valley, generate_bowl
from synthetic.terrain.crater import generate_crater


def test_flat_dem_slope_zero():
    dem = generate_flat_terrain(shape=(32, 32))
    slope = compute_slope(compute_gradients(dem))
    assert np.allclose(slope["slope_deg"], 0.0, atol=1e-8)


@pytest.mark.parametrize("angle", [5.0, 10.0])
def test_known_plane_slope_recovered(angle):
    dem = generate_slope(shape=(64, 64), angle_deg=angle)
    slope = compute_slope(compute_gradients(dem))
    interior = slope["slope_deg"][4:-4, 4:-4]
    assert np.allclose(interior, angle, atol=0.05)


def test_10deg_threshold_applied_only_after_baseline_validated():
    """§7.1: the SIH 10deg operational threshold is only meaningful after
    flat/5deg/10deg recovery is validated -- re-run those here first."""
    test_flat_dem_slope_zero()
    test_known_plane_slope_recovered(5.0)
    test_known_plane_slope_recovered(10.0)
    dem = generate_slope(shape=(64, 64), angle_deg=12.0)
    slope = compute_slope(compute_gradients(dem))
    assert (slope["slope_deg"][4:-4, 4:-4] > 10.0).all()


def test_ridge_hessian_eigenstructure():
    dem = generate_ridge(shape=(64, 64), height=20.0, width_px=8.0)
    eig = compute_eigenfeatures(compute_hessian(dem))
    cy, cx = 32, 32
    assert eig["l1"][cy, cx] < -1e-3 or eig["l2"][cy, cx] < -1e-3
    assert eig["l1"][cy, cx] >= eig["l2"][cy, cx]


def test_bowl_hessian_eigenstructure():
    dem = generate_bowl(shape=(64, 64), depth=15.0, radius_px=15.0)
    eig = compute_eigenfeatures(compute_hessian(dem))
    cy, cx = 32, 32
    assert eig["l1"][cy, cx] > 1e-4 and eig["l2"][cy, cx] > 1e-4


def test_valley_is_ridge_sign_flipped():
    ridge = generate_ridge(shape=(64, 64), height=20.0, width_px=8.0)
    valley = generate_valley(shape=(64, 64), depth=20.0, width_px=8.0)
    assert np.allclose(valley["z"], -ridge["z"])


def test_flat_gaussian_curvature_near_zero():
    dem = generate_flat_terrain(shape=(32, 32))
    curv = compute_curvature(dem)
    assert np.allclose(curv["gaussian_curvature"], 0.0, atol=1e-10)
    assert np.allclose(curv["mean_curvature"], 0.0, atol=1e-10)


def test_hessian_eigenvector_orthogonality():
    dem = generate_bowl(shape=(48, 48), depth=10.0, radius_px=12.0)
    eig = compute_eigenfeatures(compute_hessian(dem))
    dot = (eig["principal_dir1"] * eig["principal_dir2"]).sum(axis=-1)
    assert np.allclose(dot, 0.0, atol=1e-6)


def test_crater_depth_diameter_recovered_within_tolerance():
    dem = generate_crater(shape=(128, 128), diameter_px=30.0, depth=8.0, rim_height=1.5)
    gt = dem["ground_truth"]
    candidates = detect_craters(dem, depression_min_depth=1.0)
    assert len(candidates) >= 1
    best = min(candidates, key=lambda c: (c["center_row"] - gt["center_row"]) ** 2 + (c["center_col"] - gt["center_col"]) ** 2)
    center_err = np.hypot(best["center_row"] - gt["center_row"], best["center_col"] - gt["center_col"])
    assert center_err < 3.0
    assert abs(best["depth_m"] - gt["depth_m"]) / gt["depth_m"] < 0.35
    assert abs(best["diameter_px"] - gt["diameter_px"]) / gt["diameter_px"] < 0.5


def test_roughness_zero_on_flat_positive_on_bumpy():
    flat = generate_flat_terrain(shape=(32, 32))
    assert np.allclose(compute_roughness(flat, window=5), 0.0, atol=1e-10)
    from synthetic.terrain.boulder import generate_boulder
    bumpy = generate_boulder(shape=(64, 64), n_boulders=5)
    assert compute_roughness(bumpy, window=5).max() > 0.05
