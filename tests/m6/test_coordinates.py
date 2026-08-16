import pytest
import math
from lunar_hazard_mapper.m6_planner.coordinate import CoordinateTransform

def test_world_to_local_identity():
    transform = CoordinateTransform(origin_lat=0.0, origin_lon=0.0)
    
    local_coords = (10.0, -5.0, 3.14)
    world_coords = transform.local_to_world(*local_coords)
    assert world_coords == local_coords
    
    recovered = transform.world_to_local(*world_coords)
    assert recovered == local_coords

def test_geographic_to_local_origin():
    # At origin, local coordinates should be (0, 0, 0)
    transform = CoordinateTransform(origin_lat=10.0, origin_lon=20.0, origin_alt=100.0)
    x, y, z = transform.geographic_to_local(lat=10.0, lon=20.0, alt=100.0)
    assert pytest.approx(x, abs=1e-5) == 0.0
    assert pytest.approx(y, abs=1e-5) == 0.0
    assert pytest.approx(z, abs=1e-5) == 0.0

def test_geographic_to_local_distance():
    transform = CoordinateTransform(origin_lat=0.0, origin_lon=0.0, origin_alt=0.0)
    
    # 1 degree of latitude at the equator (or anywhere on sphere)
    # distance = R * theta = 1737400 * (1 * pi / 180)
    expected_dist = 1737400.0 * math.radians(1.0)
    
    x, y, z = transform.geographic_to_local(lat=1.0, lon=0.0, alt=0.0)
    assert pytest.approx(x, abs=1e-2) == 0.0
    assert pytest.approx(y, abs=1e-2) == expected_dist
    assert pytest.approx(z, abs=1e-5) == 0.0

def test_local_to_geographic():
    transform = CoordinateTransform(origin_lat=5.0, origin_lon=-5.0, origin_alt=50.0)
    
    target_lat = 5.1
    target_lon = -4.9
    target_alt = 60.0
    
    # Forward
    x, y, z = transform.geographic_to_local(target_lat, target_lon, target_alt)
    
    # Inverse
    rec_lat, rec_lon, rec_alt = transform.local_to_geographic(x, y, z)
    
    assert pytest.approx(rec_lat, abs=1e-6) == target_lat
    assert pytest.approx(rec_lon, abs=1e-6) == target_lon
    assert pytest.approx(rec_alt, abs=1e-6) == target_alt
