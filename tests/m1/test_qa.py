"""Tests for M1 QA and checksum utilities."""

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

from lunar_hazard_mapper.m1_data.checksums import build_checksum_manifest
from lunar_hazard_mapper.m1_data.qa import check_crs_exists, check_pair_alignment, check_value_range, run_qa_suite


def _write(path: Path, *, crs=None, value=0.5, transform=None):
    profile = {"driver": "GTiff", "width": 2, "height": 2, "count": 1, "dtype": "float32", "nodata": -9999.0, "transform": transform or from_origin(0, 2, 1, 1), "crs": crs}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.full((1, 2, 2), value, dtype=np.float32))


def test_crs_check_fails_without_crs(tmp_path: Path):
    path = tmp_path / "no_crs.tif"
    _write(path)
    assert not check_crs_exists(path)["passed"]


def test_value_range_fails_outside_normalised_range(tmp_path: Path):
    path = tmp_path / "bad.tif"
    _write(path, crs=CRS.from_epsg(4326), value=2.0)
    assert not check_value_range(path, 0, 1)["passed"]


def test_pair_alignment_rejects_small_hr(tmp_path: Path):
    lr, hr = tmp_path / "lr.tif", tmp_path / "hr.tif"
    _write(lr, crs=CRS.from_epsg(4326), transform=from_origin(0, 2, 1, 1))
    _write(hr, crs=CRS.from_epsg(4326), transform=from_origin(0, 1, 1, 1))
    assert not check_pair_alignment(lr, hr)["passed"]


def test_empty_manifest_qa_is_explicit(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"pairs": [], "status": "blocked_no_validated_pairs"}), encoding="utf-8")
    report = run_qa_suite(manifest, {})
    assert report["failed"] == 0
    assert report["pair_count"] == 0


def test_checksums_are_deterministic(tmp_path: Path):
    path = tmp_path / "data.bin"
    path.write_bytes(b"hello")
    first = build_checksum_manifest([path])
    second = build_checksum_manifest([path])
    assert first == second
