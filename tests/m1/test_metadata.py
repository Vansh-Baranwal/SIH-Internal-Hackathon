"""Tests for Member 1 GeoTIFF metadata inspection."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from lunar_hazard_mapper.m1_data.metadata import inspect_tiff, summarise


def _memory_tiff(*, crs="EPSG:4326"):
    """Create a small on-disk fixture through rasterio's MemoryFile."""
    memory = MemoryFile()
    with memory.open(
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype="uint8",
        crs=crs,
        transform=from_origin(10, 20, 5, 5),
        nodata=0,
    ) as dataset:
        dataset.write(np.array([[1, 1, 0, 0], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]], dtype=np.uint8), 1)
    return memory


def test_inspect_tiff_reports_metadata_and_nodata_fraction(tmp_path: Path):
    """A valid TIFF exposes CRS, transform, resolution, and mask fraction."""
    memory = _memory_tiff()
    path = tmp_path / "fixture.tif"
    path.write_bytes(memory.read())
    memory.close()

    record = inspect_tiff(path)

    assert record["crs"] == "EPSG:4326"
    assert record["has_valid_crs"] is True
    assert record["has_valid_transform"] is True
    assert record["pixel_size_x_m"] == 5.0
    assert record["pixel_size_y_m"] == 5.0
    assert record["nodata_fraction"] == 0.125


def test_inspect_tiff_detects_missing_crs(tmp_path: Path):
    """A TIFF without CRS is explicitly marked invalid."""
    memory = _memory_tiff(crs=None)
    path = tmp_path / "no_crs.tif"
    path.write_bytes(memory.read())
    memory.close()

    record = inspect_tiff(path)

    assert record["crs"] is None
    assert record["has_valid_crs"] is False


def test_summarise_aggregates_records():
    """Summary values aggregate files, dtypes, CRS, pixels, and quality flags."""
    records = [
        {"file_size_mb": 1.25, "dtype": "uint8", "crs": "EPSG:4326", "pixel_size_x_m": 5.0, "pixel_size_y_m": 5.0, "has_valid_crs": True, "has_valid_transform": True, "bounds": {"west": 0, "south": 0, "east": 2, "north": 2}},
        {"file_size_mb": 0.75, "dtype": "uint16", "crs": None, "pixel_size_x_m": None, "pixel_size_y_m": None, "has_valid_crs": False, "has_valid_transform": False, "bounds": {"west": -1, "south": -2, "east": 3, "north": 4}},
    ]

    summary = summarise(records)

    assert summary["total_files"] == 2
    assert summary["total_size_mb"] == 2.0
    assert summary["unique_dtypes"] == ["uint16", "uint8"]
    assert summary["unique_crs_values"] == ["EPSG:4326"]
    assert summary["pixel_size_range"] == {"min_m": 5.0, "max_m": 5.0}
    assert summary["any_missing_crs"] is True
    assert summary["any_missing_transform"] is True
    assert summary["bounds"] == {"west": -1.0, "south": -2.0, "east": 3.0, "north": 4.0}
