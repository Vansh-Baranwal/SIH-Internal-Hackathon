import pytest
import numpy as np
from affine import Affine

from lunar_hazard_mapper.m3_terrain.dem import DEM
from lunar_hazard_mapper.m6_planner.adapters.dem_provider import DemBackedTerrainProvider

@pytest.fixture
def geographic_dem():
    # 3x3 DEM grid representing a geographic coordinate system
    elevation = np.array([
        [100.0, 105.0, 110.0],
        [ 95.0, 100.0, 105.0],
        [-32768.0, 90.0, 95.0]
    ], dtype=np.float32)
    
    # Geographic bounds near equator
    # 1 degree lat = ~30323 meters
    # Let's say pixels are 0.001 degrees (~30m)
    transform = Affine.translation(338.67, -2.62) * Affine.scale(0.001, -0.001)
    
    return DEM(
        elevation=elevation,
        pixel_size_m=0.001, # Native units are degrees, so it's nominally degrees
        transform=transform,
        crs="GEOGCS[\"SelenoGraphic\"]",
        nodata=-32768.0,
        vertical_units="meters",
        source_type="measured"
    )

def test_dem_provider_geographic_round_trip(geographic_dem):
    """
    Validates exact mathematically sound M5 local metric -> geographic lon/lat -> raster pixel coordinate trace.
    """
    R_moon = 1737400.0
    m_per_deg_lat = R_moon * np.pi / 180.0
    
    # Calculate local scaling roughly identical to pipeline.py
    center_lat = geographic_dem.transform.f + (geographic_dem.shape[0] / 2) * geographic_dem.transform.e
    m_per_deg_lon = m_per_deg_lat * np.cos(np.radians(center_lat))
    
    provider = DemBackedTerrainProvider(
        dem=geographic_dem,
        origin_lon_deg=geographic_dem.transform.c,
        origin_lat_deg=geographic_dem.transform.f,
        m_per_deg_lon=m_per_deg_lon,
        m_per_deg_lat=m_per_deg_lat
    )
    
    # Select several known DEM pixels to round-trip
    test_pixels = [
        (0, 0),    # Top-left corner
        (1, 1),    # Center
        (0, 2),    # Top-right corner
        (1, 2),    # Middle-right edge
    ]
    
    for row, col in test_pixels:
        # 1. Pixel -> Geographic
        lon_deg, lat_deg = geographic_dem.transform * (col, row)
        
        # 2. Geographic -> Local M5 Metric Frame
        x_m = (lon_deg - provider.origin_lon_deg) * provider.m_per_deg_lon
        y_m = (provider.origin_lat_deg - lat_deg) * provider.m_per_deg_lat # Latitude decreases going down
        
        # 3. Query TerrainProvider
        h = provider.get_height(x_m, y_m)
        
        # 4. Compare physical elevations
        expected_h = geographic_dem.elevation[row, col]
        assert np.isclose(h, expected_h), f"Round-trip failed at pixel ({row}, {col})"

def test_dem_provider_nodata(geographic_dem):
    provider = DemBackedTerrainProvider(geographic_dem)
    
    # Pixel [2, 0] contains -32768.0
    # Its center is row=2, col=0
    lon_deg, lat_deg = geographic_dem.transform * (0, 2)
    x_m = (lon_deg - provider.origin_lon_deg) * provider.m_per_deg_lon
    y_m = (provider.origin_lat_deg - lat_deg) * provider.m_per_deg_lat

    with pytest.raises(ValueError, match="Nodata encountered"):
        provider.get_height(x_m, y_m)

def test_dem_provider_out_of_bounds(geographic_dem):
    provider = DemBackedTerrainProvider(geographic_dem)
    
    # Beyond the 3x3 grid
    lon_deg, lat_deg = geographic_dem.transform * (10, 10)
    x_m = (lon_deg - provider.origin_lon_deg) * provider.m_per_deg_lon
    y_m = (provider.origin_lat_deg - lat_deg) * provider.m_per_deg_lat

    with pytest.raises(ValueError, match="out of DEM bounds"):
        provider.get_height(x_m, y_m)
