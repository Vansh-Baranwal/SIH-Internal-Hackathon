"""
M6 Coordinate Convention
------------------------
This module defines the shared coordinate convention for the Lunar Hazard Mapper project.

Convention:
- Local Cartesian frame for simulation.
- X = East
- Y = North
- Z = Up
- Distance units: meters
- Time units: seconds
- Internal angles: radians
- Display angles: degrees

This module provides basic transformations to/from geographic coordinates for provenance,
and mapping logic to Blender coordinates if necessary.
"""

import math
from typing import Tuple

class CoordinateTransform:
    """
    Provides transformations between the local simulation Cartesian frame, 
    DEM coordinates, and Blender world coordinates.
    """

    def __init__(self, origin_lat: float, origin_lon: float, origin_alt: float = 0.0):
        """
        Initializes the coordinate transform.
        
        Args:
            origin_lat: Origin latitude in degrees.
            origin_lon: Origin longitude in degrees.
            origin_alt: Origin altitude in meters.
        """
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        self.origin_alt = origin_alt
        
        # Approximate lunar radius in meters
        self.R_MOON = 1737400.0

    def local_to_world(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        Converts local simulation coordinates to global world coordinates for the renderer.
        In this convention, Z is UP, and X/Y match East/North directly.
        If scale is 1:1, this is an identity transformation.
        """
        return x, y, z
    
    def world_to_local(self, bx: float, by: float, bz: float) -> Tuple[float, float, float]:
        """
        Converts world coordinates from the frontend to local simulation coordinates.
        """
        return bx, by, bz

    def geographic_to_local(self, lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """
        Approximate equirectangular projection to local Cartesian for small lunar regions.
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        orig_lat_rad = math.radians(self.origin_lat)
        orig_lon_rad = math.radians(self.origin_lon)

        x = self.R_MOON * (lon_rad - orig_lon_rad) * math.cos(orig_lat_rad)
        y = self.R_MOON * (lat_rad - orig_lat_rad)
        z = alt - self.origin_alt

        return x, y, z

    def local_to_geographic(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        Converts local Cartesian back to geographic coordinates.
        """
        orig_lat_rad = math.radians(self.origin_lat)
        orig_lon_rad = math.radians(self.origin_lon)

        lat_rad = orig_lat_rad + (y / self.R_MOON)
        lon_rad = orig_lon_rad + (x / (self.R_MOON * math.cos(orig_lat_rad)))
        alt = z + self.origin_alt

        return math.degrees(lat_rad), math.degrees(lon_rad), alt
