import pytest
from lunar_hazard_mapper.m6_planner.adapters.site_evaluator_adapter import SiteEvaluatorAdapter
from lunar_hazard_mapper.m6_planner.coordinate import CoordinateTransform
from lunar_hazard_mapper.m6_planner.schemas import LanderProfile

def test_interaction_coordinate_mapping():
    """
    Test that a click at frontend (wx, wy, wz) maps correctly to (x, y, z) 
    in local simulation space without accidental swapping (e.g. y, x).
    """
    # Simple identity transform for testing
    transform = CoordinateTransform(origin_lat=0.0, origin_lon=0.0)
    adapter = SiteEvaluatorAdapter(transform)
    
    lander = LanderProfile(
        name="TestLander",
        mass=1000.0,
        maxSlope=10.0,
        maxVz=-2.0,
        maxVxy=1.0,
        footprint=2.0,
        clearance=1.0,
        deltaVBudget=100.0,
        uncertaintyLimit=1.0, maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    wx, wy, wz = 123.0, 456.0, 10.0
    
    # Evaluate click
    result = adapter.evaluate_interaction(wx, wy, wz, lander, site_id="CLICK_01")
    
    # Assert coordinates didn't get swapped
    assert result.x == 123.0, f"Expected x to be 123.0, got {result.x}"
    assert result.y == 456.0, f"Expected y to be 456.0, got {result.y}"
    assert result.siteId == "CLICK_01"

def test_interaction_mock_feasibility():
    """Test the mock feasibility logic (safe if < 500m radius)."""
    transform = CoordinateTransform(origin_lat=0.0, origin_lon=0.0)
    adapter = SiteEvaluatorAdapter(transform)
    lander = LanderProfile(
        name="TestLander",
        mass=1000.0,
        maxSlope=10.0,
        maxVz=-2.0,
        maxVxy=1.0,
        footprint=2.0,
        clearance=1.0,
        deltaVBudget=100.0,
        uncertaintyLimit=1.0, maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    # Inside 500m
    result_safe = adapter.evaluate_interaction(0.0, 400.0, 0.0, lander)
    assert result_safe.feasible is True
    assert result_safe.score == 0.9
    
    # Outside 500m
    result_unsafe = adapter.evaluate_interaction(400.0, 400.0, 0.0, lander)
    assert result_unsafe.feasible is False
    assert result_unsafe.score == 0.2
    assert len(result_unsafe.reasons) > 0
