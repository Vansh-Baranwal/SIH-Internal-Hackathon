import pytest
from lunar_hazard_mapper.m1_data.errors import MetadataValidationError
from lunar_hazard_mapper.m1_data.metadata import inspect_raster

def test_metadata_extraction(synthetic_raster):
    m = inspect_raster(synthetic_raster)
    assert m["crs"] == "EPSG:3857"
    assert m["pixel_size_x"] == 5
    assert m["pixel_size_y"] == 5
    assert m["transform"] == [5.0, 0.0, 1000.0, 0.0, -5.0, 2000.0]
    assert m["nodata"] == -9999

def test_missing_crs_fails(tmp_path):
    import rasterio
    import numpy as np
    path = tmp_path / "no_crs.tif"
    with rasterio.open(path, "w", driver="GTiff", width=2, height=2, count=1, dtype="uint8", transform=(1,0,0,0,-1,2)) as dst: dst.write(np.ones((1,2,2),dtype="uint8"))
    with pytest.raises(MetadataValidationError, match="no CRS"):
        inspect_raster(path)
