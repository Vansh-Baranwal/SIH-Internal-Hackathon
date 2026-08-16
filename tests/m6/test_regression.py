import pytest
import numpy as np
from lunar_hazard_mapper.m6_planner.schemas import LanderProfile, ManeuverConfig, UncertaintyConfig, TrajectoryStatus
from lunar_hazard_mapper.m6_planner.reachability.delta_v import estimate_required_delta_v
from lunar_hazard_mapper.m6_planner.physics.thrust import saturate_thrust
from lunar_hazard_mapper.m6_planner.physics.integrator import simulate
from lunar_hazard_mapper.m6_planner.adapters.terrain_provider import MockTerrainProvider
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory

@pytest.fixture
def base_lander():
    return LanderProfile(
        name="TestLander", mass=1000.0, maxSlope=15.0, maxVz=-3.0, maxVxy=2.0,
        footprint=3.0, clearance=1.0, deltaVBudget=1000.0,
        maxThrust=3000.0, isp=311.0, maxTiltAngle=45.0
    )

def test_delta_v_invalid_time():
    """Test that maneuver time below minimum returns infinity."""
    pos = np.zeros(3)
    target = np.array([100.0, 100.0, 0.0])
    
    config = ManeuverConfig(maneuverTime=0.5) # Invalid short time
    dv = estimate_required_delta_v(pos, pos, target, config)
    assert dv == float('inf')
    
def test_thrust_tilt_constraint():
    """Test geometric tilt constraint."""
    # Requested thrust has large lateral component
    req = np.array([5000.0, 0.0, 1000.0])
    
    # 45 deg tilt means max horizontal = vertical (1000)
    constrained = saturate_thrust(req, max_thrust=10000.0, max_tilt_angle_deg=45.0)
    
    assert constrained[0] == pytest.approx(1000.0)
    assert constrained[2] == 1000.0
    
def test_lander_max_thrust_used(base_lander):
    """Test that max thrust is enforced on total magnitude."""
    req = np.array([0.0, 0.0, 10000.0])
    constrained = saturate_thrust(req, base_lander.maxThrust, base_lander.maxTiltAngle)
    
    assert np.linalg.norm(constrained) == pytest.approx(base_lander.maxThrust)

def test_terrain_height_adapter():
    """Test that the terrain provider returns expected height."""
    provider = MockTerrainProvider(15.0)
    assert provider.get_height(0, 0) == 15.0

def test_successful_touchdown_status(base_lander):
    """Test SUCCESS status for valid landing."""
    initial = np.array([0.0, 0.0, 50.0, 0.0, 0.0, 0.0])
    target = np.array([0.0, 0.0, 0.0])
    
    traj = generate_trajectory(initial, target, base_lander, "TARGET_A", ManeuverConfig())
    assert traj.status == TrajectoryStatus.SUCCESS

def test_ground_collision_status(base_lander):
    """Test GROUND_COLLISION if landing with high velocity."""
    # Start high up with huge downward velocity and insufficient thrust to stop
    initial = np.array([0.0, 0.0, 50.0, 0.0, 0.0, -50.0])
    target = np.array([0.0, 0.0, 0.0])
    
    base_lander.maxThrust = 100.0 # Very weak engine
    traj = generate_trajectory(initial, target, base_lander, "TARGET_A", ManeuverConfig())
    
    assert traj.status == TrajectoryStatus.GROUND_COLLISION

def test_timeout_status(base_lander):
    """Test TIMEOUT if simulation ends before ground contact."""
    # Start very high, weak gravity, short duration
    initial = np.array([0.0, 0.0, 10000.0, 0.0, 0.0, 0.0])
    target = np.array([0.0, 0.0, 0.0])
    
    config = ManeuverConfig(maxDuration=5.0)
    traj = generate_trajectory(initial, target, base_lander, "TARGET_A", config)
    
    assert traj.status == TrajectoryStatus.TIMEOUT

def test_uncertainty_config():
    from lunar_hazard_mapper.m6_planner.uncertainty.noise import apply_sensor_noise
    state = np.zeros(6)
    config = UncertaintyConfig(position_std_m=0.0, altitude_std_m=5.0, velocity_std_mps=0.0)
    
    noisy = apply_sensor_noise(state, config, seed=1)
    
    assert noisy[0] == 0.0
    assert noisy[1] == 0.0
    assert noisy[2] != 0.0
    assert noisy[3] == 0.0
