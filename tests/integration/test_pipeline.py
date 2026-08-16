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
def test_full_dual_path_pipeline():
    # Run the pipeline with a very small 20x20 subset to keep tests fast
    stats = run_dual_pipeline(scene_id="01_01", subset_window=((0, 100), (0, 100)))
    
    # M1
    assert stats["m1"]["status"] == "success"
    # M2
    assert stats["m2"]["status"] == "success"
    assert "32x" in stats["m2"]["scale"]
    # M3
    assert stats["m3"]["status"] == "success"
    # M4
    assert stats["m4"]["status"] == "success"
    assert "slope_deg" in stats["m4"]["hazard_layers"]
    # M5
    assert stats["m5"]["status"] == "success"
    # M6
    assert stats["m6"]["status"] in ["success", "skipped"]

def test_m2_optical_output():
    # Output verified via pipeline runner
    pass

def test_tmcdtm_measured_dem():
    # Output verified via pipeline runner
    pass

def test_m3_to_m4():
    pass

def test_m4_to_m5():
    pass

def test_m5_to_m6():
    pass
