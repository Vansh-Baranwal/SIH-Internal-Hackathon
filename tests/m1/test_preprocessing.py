"""Tests for M1 radiometric normalization."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

from lunar_hazard_mapper.m1_data.preprocessing import (
    compute_normalisation_stats,
    normalise_tile,
    preprocess_tile,
)


def test_normalise_tile_range_and_nodata():
    data = np.array([[0, 5, 10], [-9999, 7, 20]], dtype=np.float32)
    result = normalise_tile(data, data == -9999, 0, 10)
    assert result.dtype == np.float32
    assert np.allclose(result[0], [0, 0.5, 1])
    assert result[1, 0] == -9999
    assert result[1, 2] == 1


def test_all_nodata_stats_fail(tmp_path: Path):
    path = tmp_path / "all_nodata.tif"
    profile = {"driver": "GTiff", "width": 2, "height": 2, "count": 1, "dtype": "float32", "nodata": -9999, "transform": from_origin(0, 2, 1, 1), "crs": CRS.from_epsg(4326)}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.full((1, 2, 2), -9999, dtype=np.float32))
    try:
        compute_normalisation_stats([path], 2, 98, -9999)
    except ValueError:
        pass
    else:
        raise AssertionError("expected all-nodata statistics to fail")


def test_stats_are_independent(tmp_path: Path):
    paths = []
    for index, value in enumerate((0, 100)):
        path = tmp_path / f"tile{index}.tif"
        profile = {"driver": "GTiff", "width": 2, "height": 2, "count": 1, "dtype": "float32", "nodata": -9999, "transform": from_origin(0, 2, 1, 1), "crs": CRS.from_epsg(4326)}
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(np.full((1, 2, 2), value, dtype=np.float32))
        paths.append(path)
    assert compute_normalisation_stats([paths[0]], 0, 100, -9999)["p_low"] != compute_normalisation_stats([paths[1]], 0, 100, -9999)["p_low"]


def test_preprocess_preserves_geospatial_metadata(tmp_path: Path):
    source, output = tmp_path / "source.tif", tmp_path / "out.tif"
    profile = {"driver": "GTiff", "width": 2, "height": 2, "count": 1, "dtype": "uint16", "nodata": 0, "transform": from_origin(10, 20, 2, 2), "crs": CRS.from_epsg(4326)}
    with rasterio.open(source, "w", **profile) as dst:
        dst.write(np.array([[[1, 2], [3, 4]]], dtype=np.uint16))
    result = preprocess_tile(source, output, {"p_low": 1, "p_high": 4}, -9999)
    assert result["success"]
    with rasterio.open(output) as raster:
        assert raster.crs == CRS.from_epsg(4326)
        assert raster.transform == from_origin(10, 20, 2, 2)
        assert raster.dtypes[0] == "float32"
        assert raster.tags()["preprocessing"] == "radiometric_normalisation_v1"
