import pytest
from lunar_hazard_mapper.m1_data.contract import validate_tile_contract
from lunar_hazard_mapper.m1_data.errors import DataContractError
from lunar_hazard_mapper.m1_data.qa import run_qa
from lunar_hazard_mapper.m1_data.tiling import create_tiles

def test_contract_and_qa(synthetic_raster, tmp_path):
    records = create_tiles(synthetic_raster, tmp_path / "tiles", tile_width=128, tile_height=128)
    report = run_qa(records)
    assert report["status"] == "PASS"

def test_contract_requires_provenance():
    with pytest.raises(DataContractError, match="source_checksum"):
        validate_tile_contract({"schema_version": "1.0", "tile_id": "x", "path": "x", "width": 1, "height": 1, "pixel_size_x": 1, "pixel_size_y": 1, "crs": "EPSG:3857", "transform": [1,0,0,0,-1,1], "origin": {"x":0,"y":0}, "nodata": None, "source_id":"x", "preprocessing_config":"none", "reference_data_available":False})
