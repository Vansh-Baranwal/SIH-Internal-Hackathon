import numpy as np
import rasterio
from lunar_hazard_mapper.m1_data.preprocessing import preprocess_raster

def test_preprocessing_is_deterministic_and_geospatial(synthetic_raster, tmp_path):
    config = {"preprocessing": {"nodata": {"enabled": True}, "normalization": {"enabled": True, "method": "percentile", "lower": 1, "upper": 99}, "dtype": {"output": "float32"}}}
    a = preprocess_raster(synthetic_raster, tmp_path / "a.tif", config)
    b = preprocess_raster(synthetic_raster, tmp_path / "b.tif", config)
    assert a["transform"] == b["transform"]
    with rasterio.open(tmp_path / "a.tif") as ds:
        values = ds.read(1)
        assert np.isnan(values[:8, :8]).all()
        assert np.nanmin(values) >= 0 and np.nanmax(values) <= 1
