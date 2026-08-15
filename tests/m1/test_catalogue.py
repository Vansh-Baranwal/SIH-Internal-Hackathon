"""Tests for the Phase 2 source catalogue."""

import json
from pathlib import Path

from lunar_hazard_mapper.m1_data.catalogue import (
    build_catalogue,
    find_overlapping_hr_tiles,
    validate_crs_consistency,
)


def bounds(west, south, east, north):
    return {"west": west, "south": south, "east": east, "north": north}


def test_overlap_and_edge_touching():
    tmc = {"file_path": "tmc.tif", "bounds": bounds(0, 0, 10, 10)}
    hr = [
        {"file_path": "overlap.tif", "bounds": bounds(1, 1, 6, 6)},
        {"file_path": "edge.tif", "bounds": bounds(10, 0, 20, 10)},
        {"file_path": "outside.tif", "bounds": bounds(20, 20, 30, 30)},
    ]
    assert find_overlapping_hr_tiles(tmc, hr) == ["overlap.tif"]


def test_crs_consistency():
    records = [
        {"source_product": "TMC_ORTHO", "crs": "EPSG:1"},
        {"source_product": "TMC_ORTHO", "crs": "EPSG:1"},
        {"source_product": "HR_ORTHO", "crs": "EPSG:2"},
        {"source_product": "HR_ORTHO", "crs": "EPSG:3"},
    ]
    result = validate_crs_consistency(records)
    assert result["TMC_ORTHO"]["is_consistent"]
    assert not result["HR_ORTHO"]["is_consistent"]


def test_build_catalogue_flags_records(tmp_path: Path):
    manifests = {
        "TMCORTHO5-1": [{"file_path": "tmc.tif", "bounds": bounds(0, 0, 10, 10), "crs": "LUNAR", "has_valid_crs": True, "has_valid_transform": True}],
        "ORTHONAC0.5-1": [{"file_path": "hr.tif", "bounds": bounds(1, 1, 6, 6), "crs": "LUNAR", "has_valid_crs": True, "has_valid_transform": True}],
        "NAC": [{"file_path": "nac.tif", "bounds": bounds(0, 0, 1, 1), "crs": None, "has_valid_crs": False, "has_valid_transform": True}],
        "TMCDTM": [{"file_path": "dem.tif", "bounds": bounds(0, 0, 1, 1), "crs": "LUNAR", "has_valid_crs": True, "has_valid_transform": True}],
    }
    for dataset, records in manifests.items():
        (tmp_path / f"inspection_{dataset}.json").write_text(json.dumps({"dataset": dataset, "records": records}))
    catalogue = build_catalogue(tmp_path)
    assert set(catalogue["stats"]) == {"TMC_ORTHO", "HR_ORTHO", "NAC", "DEM"}
    assert catalogue["stats"]["TMC_ORTHO"]["reference_available"] == 1
    assert catalogue["stats"]["NAC"]["excluded"] == 1
