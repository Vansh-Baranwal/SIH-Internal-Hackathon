import pytest
import numpy as np
from pathlib import Path
import rasterio

from lunar_hazard_mapper.api.alignment import align_rasters
from lunar_hazard_mapper.api.pipeline import run_dual_pipeline

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_DIR = BASE_DIR.parent / "Different Repo" / "SIH" / "CODE_SIH1519_ORION SPACE SYSTEM"

OPTICAL_PATH = REPO_DIR / "TMCORTHO5-1" / "TMCORTHO5-1" / "TMCORTHO5-1" / "TMCORTHOCH_01_01.tif"
DEM_PATH = REPO_DIR / "TMCDTM" / "TMCDTM" / "TMCDTM_01_01.tif"

@pytest.mark.skipif(not OPTICAL_PATH.exists() or not DEM_PATH.exists(), reason="Real dataset not found locally")
def test_tmc_ortho_tmcdtm_alignment():
    # Verify bounds are identical
    with rasterio.open(OPTICAL_PATH) as opt, rasterio.open(DEM_PATH) as dem:
        assert np.isclose(opt.bounds.left, dem.bounds.left)
        assert np.isclose(opt.bounds.bottom, dem.bounds.bottom)
        assert np.isclose(opt.bounds.right, dem.bounds.right)
        assert np.isclose(opt.bounds.top, dem.bounds.top)
        
        assert opt.crs == dem.crs

@pytest.mark.skipif(not OPTICAL_PATH.exists() or not DEM_PATH.exists(), reason="Real dataset not found locally")
def test_full_dual_path_pipeline_blocked_missing_state():
    # CASE A: No initial_state provided. Must block M6 legitimately.
    stats = run_dual_pipeline(scene_id="01_01", subset_window=((0, 100), (0, 100)))
    
    assert stats["m3"]["status"] == "success"
    assert stats["m5"]["status"] == "success"
    
    # If there are candidates, M6 must block due to missing initial state
    if stats["m5"]["candidates_found"] > 0:
        assert stats["m6"]["status"] == "blocked"
        assert "Missing initial mission state" in stats["m6"]["trajectory"]["reason"]

@pytest.mark.skipif(not OPTICAL_PATH.exists() or not DEM_PATH.exists(), reason="Real dataset not found locally")
def test_full_dual_path_pipeline_explicit_state():
    # CASE B: Explicit test initial_state provided. Must run real M6 physics.
    test_initial_state = [0.0, 0.0, 15000.0, 100.0, 0.0, -10.0]
    stats = run_dual_pipeline(scene_id="01_01", subset_window=((0, 100), (0, 100)), initial_state=test_initial_state)
    
    m6_status = stats["m6"]["status"]
    
    # Valid M6 statuses based on true trajectory integration
    valid_m6_statuses = ["success", "blocked", "ground_collision", "timeout", "invalid", "no_candidates"]
    assert m6_status in valid_m6_statuses
    
    trajectory_info = stats["m6"]["trajectory"]
    if m6_status != "no_candidates" and m6_status != "blocked" and m6_status != "invalid":
        assert trajectory_info["reachable"] is True
        assert "delta_v" in trajectory_info
        assert isinstance(trajectory_info["delta_v"], float)
        assert "points_count" in trajectory_info
        assert trajectory_info["points_count"] > 0
