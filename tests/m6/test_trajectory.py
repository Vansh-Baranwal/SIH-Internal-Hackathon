import pytest
import numpy as np
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
from lunar_hazard_mapper.m6_planner.trajectory.constraints import validate_touchdown
from lunar_hazard_mapper.m6_planner.schemas import LanderProfile

def test_trajectory_generation_and_touchdown():
    """
    Test generating a trajectory using the baseline PD controller and verifying 
    it meets the required touchdown constraints.
    """
    initial_state = np.array([0.0, 0.0, 100.0, 2.0, 0.0, 0.0]) # Hovering at 100m, moving East at 2m/s
    target_pos = np.array([50.0, 0.0, 0.0]) # Target is 50m East, ground level
    
    lander = LanderProfile(
        name="TestLander",
        mass=1000.0,
        maxSlope=10.0,
        maxVz=-2.0,       # Must land softer than 2m/s
        maxVxy=1.0,       # Must land with minimal horizontal velocity
        footprint=2.0,
        clearance=1.0,
        deltaVBudget=500.0,
        uncertaintyLimit=1.0, maxThrust=5000.0, isp=311.0, maxTiltAngle=45.0
    )
    
    from lunar_hazard_mapper.m6_planner.schemas import ManeuverConfig
    # 1. Generate trajectory
    config = ManeuverConfig(maxDuration=30.0)
    trajectory = generate_trajectory(
        initial_state=initial_state,
        target_pos=target_pos,
        lander=lander,
        target_site_id="TEST_SITE",
        maneuver_config=config
    )
    
    # 2. Validate trajectory output schema
    assert trajectory.targetSiteId == "TEST_SITE"
    assert len(trajectory.points) > 10
    
    # 3. Validate touchdown
    success, reasons = validate_touchdown(trajectory, lander, target_x=target_pos[0], target_y=target_pos[1])
    
    # We expect the PD controller to be able to hit the target safely 
    # (since limits and thrust are generous in this mock test)
    assert success is True, f"Touchdown validation failed: {reasons}"
