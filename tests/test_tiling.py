import json
import rasterio
from rasterio.transform import rowcol, xy
from lunar_hazard_mapper.m1_data.tiling import create_tiles

def test_tiles_preserve_window_transforms(synthetic_raster, tmp_path):
    records = create_tiles(synthetic_raster, tmp_path / "tiles", tile_size=64) if False else create_tiles(synthetic_raster, tmp_path / "tiles", tile_width=64, tile_height=64)
    assert len(records) == 16
    source = rasterio.open(synthetic_raster)
    first = records[0]
    assert first["origin"] == {"x": 0, "y": 0}
    assert first["transform"] == [5.0, 0.0, 1000.0, 0.0, -5.0, 2000.0]
    last = records[-1]
    assert last["origin"] == {"x": 192, "y": 192}
    with rasterio.open(last["path"]) as tile:
        sx, sy = 200, 200
        mx, my = xy(source.transform, sy + 0.5, sx + 0.5)
        tr, tc = rowcol(tile.transform, mx, my)
        assert abs(int(tr) - (sy - 192)) <= 1
        assert abs(int(tc) - (sx - 192)) <= 1
