import numpy as np
from lunar_hazard_mapper.m6_planner.adapters.terrain_provider import TerrainProvider
from lunar_hazard_mapper.m3_terrain.dem import DEM

class DemBackedTerrainProvider(TerrainProvider):
    """
    TerrainProvider implementation backed by M3's actual physical DEM.
    Converts M6 local Cartesian metric coordinates (x, y) into geographic (lon, lat)
    and then maps back into pixel indices using the DEM's geographic affine transform.
    """
    def __init__(
        self,
        dem: DEM,
        origin_lon_deg: float = None,
        origin_lat_deg: float = None,
        m_per_deg_lon: float = None,
        m_per_deg_lat: float = None
    ):
        self.dem = dem
        # The affine transform from M3 maps (col, row) to Geographic (lon, lat).
        # We invert it so we can map (lon, lat) back to (col, row).
        self.inv_transform = ~dem.transform
        
        self.origin_lon_deg = origin_lon_deg if origin_lon_deg is not None else dem.transform.c
        self.origin_lat_deg = origin_lat_deg if origin_lat_deg is not None else dem.transform.f
        
        # If explicit metric scaling wasn't provided (e.g. tests), default to the 1-to-1 assumption
        # or calculate it safely.
        if m_per_deg_lon is None or m_per_deg_lat is None:
            R_moon = 1737400.0
            self.m_per_deg_lat = R_moon * np.pi / 180.0
            
            # Use raster center for local longitudinal scale
            center_lat = dem.transform.f + (dem.shape[0] / 2) * dem.transform.e
            self.m_per_deg_lon = self.m_per_deg_lat * np.cos(np.radians(center_lat))
        else:
            self.m_per_deg_lon = m_per_deg_lon
            self.m_per_deg_lat = m_per_deg_lat
            
    def get_height(self, x: float, y: float) -> float:
        """
        Queries the TMCDTM elevation at local metric Cartesian coordinates (x, y).
        
        Steps:
        1. Convert local metric (x, y) back into geographic (lon, lat).
        2. Invert the M3 geographic transform to find floating-point (col, row).
        3. Round to nearest integer array indices.
        """
        # Note: M4/M5 treats y as positive going down. 
        # Since Latitude goes DOWN as array rows increase, we correctly subtract (y / m_per_deg_lat).
        # We also inspect the transform's E scale. If E is negative (North-up), then row*e subtracts from origin_lat.
        # This matches the M4 derivation where y_m increases positively downwards.
        
        # Convert local metric x, y to geographic degrees relative to anchor
        lon_deg = self.origin_lon_deg + (x / self.m_per_deg_lon)
        lat_deg = self.origin_lat_deg - (y / self.m_per_deg_lat)
        
        # Map geographic coordinates back to array indices using inverse affine
        col_float, row_float = self.inv_transform * (lon_deg, lat_deg)
        
        col_idx = int(round(col_float))
        row_idx = int(round(row_float))
        
        rows, cols = self.dem.shape
        if 0 <= row_idx < rows and 0 <= col_idx < cols:
            val = self.dem.elevation[row_idx, col_idx]
            if val != self.dem.nodata and not np.isnan(val):
                return float(val)
            else:
                raise ValueError(f"Nodata encountered at terrain query ({x}, {y})")
        else:
            raise ValueError(f"Terrain query ({x}, {y}) is out of DEM bounds")
