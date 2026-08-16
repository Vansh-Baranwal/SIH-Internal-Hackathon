"""Tests for M1 GeoTIFF tiling."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

from lunar_hazard_mapper.m1_data.tiling import match_hr_to_lr_tile, tile_tiff


def make_source(path: Path, width=100, height=100, nodata=None):
    profile = {
        "driver": "GTiff", "width": width, "height": height, "count": 1,
        "dtype": "float32", "crs": CRS.from_epsg(4326),
        "transform": from_origin(100, 200, 2, 2), "nodata": nodata,
    }
    with rasterio.open(path, "w", **profile) as dst:
        data = np.ones((height, width), dtype="float32")
        if nodata is not None:
            data[:, :10] = nodata
        dst.write(data, 1)


def test_tiles_preserve_metadata_and_pad_edges(tmp_path):
    source = tmp_path / "source.tif"
    make_source(source)
    records = tile_tiff(source, tmp_path / "tiles", 32, 8, 0.8, -9999)
    assert len(records) == 16
    assert all(record["origin_x"] is not None and record["origin_y"] is not None for record in records)
    with rasterio.open(records[0]["tile_path"]) as tile:
        assert tile.width == tile.height == 32
        assert tile.crs == CRS.from_epsg(4326)
        assert tile.transform.c == 100
        assert tile.transform.f == 200
        assert tile.compression.value == "LZW"


def test_nodata_windows_are_skipped(tmp_path):
    source = tmp_path / "source.tif"
    make_source(source, width=32, height=32, nodata=-9999)
    records = tile_tiff(source, tmp_path / "tiles", 32, 0, 0.8, -9999)
    assert records == []


def test_match_requires_positive_area():
    lr = {"bounds": {"west": 0, "south": 0, "east": 10, "north": 10}}
    hr = [
        {"tile_path": "overlap", "bounds": {"west": 1, "south": 1, "east": 2, "north": 2}},
        {"tile_path": "edge", "bounds": {"west": 10, "south": 0, "east": 20, "north": 10}},
    ]
    assert [item["tile_path"] for item in match_hr_to_lr_tile(lr, hr)] == ["overlap"]
