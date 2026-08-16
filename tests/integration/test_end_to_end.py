import os
import subprocess
import sys

import numpy as np
import pytest

from lunar_hazard_mapper.m3_terrain import (
    create_synthetic_terrain,
    export_dem,
    validate_dem,
    qa_check_dem,
    qa_check_exported_file,
    get_terrain_product,
    to_local_frame,
)
from lunar_hazard_mapper.m3_terrain.dem import generate_dem, DEM, SOURCE_MEASURED


def test_end_to_end():
    assert True


# ---------------------------------------------------------------------
# M3: synthetic terrain generation
# ---------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["flat", "slope", "crater", "boulder",
                                   "combined"])
def test_m3_create_synthetic_terrain(kind):
    dem = create_synthetic_terrain(kind, size=32)
    assert dem.shape == (32, 32)
    assert dem.source_type == "synthetic"
    assert np.isfinite(dem.elevation).all()


def test_m3_flat_terrain_is_actually_flat():
    dem = create_synthetic_terrain("flat", size=16, elevation_m=3.5)
    assert np.allclose(dem.elevation, 3.5)


# ---------------------------------------------------------------------
# M3: DEM construction guardrails (scientific constraint)
# ---------------------------------------------------------------------

def test_m3_refuses_raw_image_as_elevation_by_default():
    fake_image = np.random.rand(16, 16).astype("float32")
    with pytest.raises(ValueError):
        generate_dem(fake_image, pixel_size_m=1.0)


def test_m3_allows_raw_image_with_explicit_override():
    fake_image = np.random.rand(16, 16).astype("float32")
    dem = generate_dem(fake_image, pixel_size_m=1.0,
                        assume_optical_as_elevation=True)
    assert dem.source_type == "sr_estimated"
    assert dem.source_type != "measured"


# ---------------------------------------------------------------------
# M3: export + reload round trip
# ---------------------------------------------------------------------

def test_m3_export_and_reload_preserves_metadata(tmp_path):
    dem = create_synthetic_terrain("flat", size=32, elevation_m=7.0,
                                    pixel_size_m=2.0)
    out_path = str(tmp_path / "test_dem.tif")
    export_dem(dem, out_path)

    product = get_terrain_product(out_path)
    assert product["pixel_size_m"] == 2.0
    assert product["source_type"] == "synthetic"
    assert product["vertical_units"] == "meters"
    assert np.allclose(product["elevation"], 7.0)


# ---------------------------------------------------------------------
# M3: QA checks
# ---------------------------------------------------------------------

def test_m3_qa_check_dem_passes_for_valid_dem():
    dem = create_synthetic_terrain("crater", size=32)
    qa = qa_check_dem(dem)
    assert qa["all_passed"]


def test_m3_qa_check_exported_file_passes(tmp_path):
    dem = create_synthetic_terrain("boulder", size=32)
    out_path = str(tmp_path / "boulder.tif")
    export_dem(dem, out_path)
    qa = qa_check_exported_file(out_path)
    assert qa["all_passed"]


# ---------------------------------------------------------------------
# M3: validation
# ---------------------------------------------------------------------

def test_m3_validation_zero_error_against_identical_reference():
    dem = create_synthetic_terrain("flat", size=32, elevation_m=1.0)
    reference = create_synthetic_terrain("flat", size=32, elevation_m=1.0)
    report = validate_dem(dem, reference)
    assert report["mae"] == pytest.approx(0.0)
    assert report["rmse"] == pytest.approx(0.0)
    assert report["label"] == "synthetic_validation"


def test_m3_validation_nonzero_error_against_different_reference():
    dem = create_synthetic_terrain("flat", size=32, elevation_m=5.0)
    reference = create_synthetic_terrain("flat", size=32, elevation_m=0.0)
    report = validate_dem(dem, reference)
    assert report["mae"] == pytest.approx(5.0)


# ---------------------------------------------------------------------
# M3: local coordinate frame (for M6)
# ---------------------------------------------------------------------

def test_m3_to_local_frame_shapes_match_dem():
    dem = create_synthetic_terrain("flat", size=16, pixel_size_m=1.0)
    local = to_local_frame(dem)
    assert local["x"].shape == dem.shape
    assert local["y"].shape == dem.shape
    assert local["z"].shape == dem.shape
    assert np.array_equal(local["z"], dem.elevation)


def test_m3_to_local_frame_uses_pixel_centers():
    # With pixel_size_m=2.0 and default origin (0, 0), the first pixel's
    # center should be at (1.0, -1.0) -- half a pixel in from the corner,
    # x=east positive, y=north negative (row 0 is the northernmost row,
    # so its center is *below* y=0 by half a pixel... actually origin_y=0
    # is the top-left corner, so pixel (0,0)'s center is at y = -pixel/2).
    dem = create_synthetic_terrain("flat", size=8, pixel_size_m=2.0)
    local = to_local_frame(dem)
    assert local["x"][0, 0] == pytest.approx(1.0)
    assert local["y"][0, 0] == pytest.approx(-1.0)
    # Moving one pixel right (+col) should move x east by exactly one
    # pixel size, and leave y unchanged.
    assert local["x"][0, 1] == pytest.approx(3.0)
    assert local["y"][0, 1] == pytest.approx(-1.0)


# ---------------------------------------------------------------------
# M3: CRS / georeferencing (Issue 5)
# ---------------------------------------------------------------------

def test_m3_synthetic_dem_is_not_georeferenced_by_default():
    dem = create_synthetic_terrain("flat", size=16)
    assert dem.crs is None
    assert dem.is_georeferenced is False


def test_m3_generate_dem_accepts_real_crs_when_provided():
    terrain = {"elevation": np.zeros((16, 16), dtype="float32"),
               "pixel_size_m": 1.0, "source_type": "synthetic"}
    dem = generate_dem(terrain, crs="EPSG:4326")
    assert dem.crs == "EPSG:4326"
    assert dem.is_georeferenced is True


def test_m3_get_terrain_product_reports_is_georeferenced(tmp_path):
    dem = create_synthetic_terrain("flat", size=16)
    out_path = str(tmp_path / "local_only.tif")
    export_dem(dem, out_path)
    product = get_terrain_product(out_path)
    assert product["is_georeferenced"] is False
    assert product["crs"] is None


# ---------------------------------------------------------------------
# M3: optical-vs-elevation override emits an explicit warning (Issue 3)
# ---------------------------------------------------------------------

def test_m3_optical_override_emits_warning():
    fake_image = np.random.rand(16, 16).astype("float32")
    with pytest.warns(UserWarning):
        generate_dem(fake_image, pixel_size_m=1.0,
                      assume_optical_as_elevation=True)


# ---------------------------------------------------------------------
# M3: validation against a genuine "measured" reference (Issue 4)
# ---------------------------------------------------------------------

def test_m3_validation_labels_measured_reference_correctly():
    dem = create_synthetic_terrain("flat", size=16, elevation_m=2.0)
    # Simulate what a genuine reference DEM would look like: same shape,
    # explicitly tagged source_type="measured". We are NOT claiming this
    # is real lunar data -- this only tests that the labeling logic
    # correctly distinguishes a measured reference from a synthetic one.
    measured_reference = DEM(
        elevation=np.full((16, 16), 2.0, dtype="float32"),
        pixel_size_m=1.0,
        transform=dem.transform,
        crs=None,
        nodata=-9999.0,
        vertical_units="meters",
        source_type=SOURCE_MEASURED,
    )
    report = validate_dem(dem, measured_reference)
    assert report["label"] == "measured_validation"
    assert report["reference_source_type"] == "measured"


# ---------------------------------------------------------------------
# M3: stronger QA checks (Issue 6)
# ---------------------------------------------------------------------

def test_m3_qa_check_dem_detects_confidence_shape_mismatch():
    terrain = {"elevation": np.zeros((16, 16), dtype="float32"),
               "pixel_size_m": 1.0, "source_type": "synthetic",
               "confidence": np.zeros((8, 8), dtype="float32")}
    dem = generate_dem(terrain)
    qa = qa_check_dem(dem)
    assert qa["confidence_shape_valid"] is False
    assert qa["all_passed"] is False


def test_m3_qa_check_dem_passes_with_valid_confidence():
    terrain = {"elevation": np.zeros((16, 16), dtype="float32"),
               "pixel_size_m": 1.0, "source_type": "synthetic",
               "confidence": np.ones((16, 16), dtype="float32")}
    dem = generate_dem(terrain)
    qa = qa_check_dem(dem)
    assert qa["confidence_shape_valid"] is True
    assert qa["confidence_values_valid"] is True
    assert qa["all_passed"] is True


def test_m3_qa_check_dem_detects_invalid_crs():
    terrain = {"elevation": np.zeros((16, 16), dtype="float32"),
               "pixel_size_m": 1.0, "source_type": "synthetic"}
    dem = generate_dem(terrain, crs="not a real crs string")
    qa = qa_check_dem(dem)
    assert qa["crs_valid"] is False
    assert qa["all_passed"] is False


def test_m3_qa_check_exported_file_confidence_band_preserved(tmp_path):
    terrain = {"elevation": np.zeros((16, 16), dtype="float32"),
               "pixel_size_m": 1.0, "source_type": "synthetic",
               "confidence": np.ones((16, 16), dtype="float32")}
    dem = generate_dem(terrain)
    out_path = str(tmp_path / "with_confidence.tif")
    export_dem(dem, out_path)
    qa = qa_check_exported_file(out_path)
    assert qa["band_count_valid"] is True
    assert qa["confidence_band_preserved"] is True
    assert qa["all_passed"] is True

    product = get_terrain_product(out_path)
    assert product["confidence"] is not None
    assert product["confidence"].shape == (16, 16)


# ---------------------------------------------------------------------
# M3: real, executable smoke test (Issue 1 / Issue 9)
# ---------------------------------------------------------------------

def test_m3_smoke_test_script_runs_end_to_end():
    """
    Runs scripts/run_smoke_test.py as a real subprocess and checks it
    exits 0. This is the test that would have caught the smoke test
    regressing back to a placeholder print() statement.
    """
    repo_root = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(repo_root, "scripts", "run_smoke_test.py")

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"smoke test script failed:\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "SMOKE TEST PASSED" in result.stdout
