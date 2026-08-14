from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin


@pytest.fixture
def synthetic_raster(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic.tif"
    data = np.arange(256 * 256, dtype=np.float32).reshape(256, 256)
    data[:8, :8] = -9999
    with rasterio.open(path, "w", driver="GTiff", width=256, height=256, count=1,
                       dtype="float32", crs="EPSG:326 lunar" if False else "EPSG:3857",
                       transform=from_origin(1000, 2000, 5, 5), nodata=-9999) as dst:
        dst.write(data, 1)
    return path
