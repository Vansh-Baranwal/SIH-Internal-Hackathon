"""Tests for evidence-gated M1 training-pair construction."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

from lunar_hazard_mapper.m1_data.pairs import build_pairs_manifest, co_register_pair, spatial_split


def _raster(path: Path, transform, crs, value: float, pixel: float = 1.0):
    profile = {"driver": "GTiff", "width": 4, "height": 4, "count": 1, "dtype": "float32", "nodata": -9999.0, "transform": transform, "crs": crs}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.full((1, 4, 4), value, dtype=np.float32))


def test_co_register_pair_matches_lr_grid(tmp_path: Path):
    lr_path, hr_path = tmp_path / "lr.tif", tmp_path / "hr.tif"
    transform = from_origin(0, 4, 1, 1)
    _raster(lr_path, transform, CRS.from_epsg(4326), 1)
    _raster(hr_path, transform, CRS.from_epsg(4326), 2)
    lr_out, hr_out = tmp_path / "out/lr.tif", tmp_path / "out/hr.tif"
    result = co_register_pair({"tile_path": str(lr_path)}, {"tile_path": str(hr_path)}, lr_out, hr_out)
    assert result and hr_out.exists()
    with rasterio.open(hr_out) as raster:
        assert raster.crs == CRS.from_epsg(4326)
        assert raster.transform == transform
        assert raster.shape == (4, 4)


def test_spatial_split_requires_explicit_regions():
    pair = {"geographic_bounds": [0, 0, 1, 1]}
    try:
        spatial_split([pair], {"spatial_split": {"train_region": None, "val_region": None, "test_region": None}})
    except ValueError:
        pass
    else:
        raise AssertionError("missing split bounds must be rejected")


def test_build_empty_manifest_is_explicit(tmp_path: Path):
    manifest = build_pairs_manifest([], tmp_path / "manifest.json", status="blocked_no_validated_pairs", failure_reasons=["no overlap"])
    assert manifest["total_pairs"] == 0
    assert manifest["status"] == "blocked_no_validated_pairs"
    assert manifest["failure_reasons"] == ["no overlap"]
