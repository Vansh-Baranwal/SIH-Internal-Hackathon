import pytest
import numpy as np
from lunar_hazard_mapper.m6_planner.physics.constants import GRAVITY_MOON
from lunar_hazard_mapper.m6_planner.physics.dynamics import compute_derivatives
from lunar_hazard_mapper.m6_planner.physics.thrust import (
    saturate_thrust, 
    get_zero_thrust_profile, 
    get_constant_thrust_profile
)
from lunar_hazard_mapper.m6_planner.physics.integrator import simulate

def test_free_fall():
    """
    Test 1 - Free Fall: Thrust = 0
    Expected vertical acceleration = -1.62 m/s^2
    """
    state = np.array([0.0, 0.0, 1000.0, 0.0, 0.0, 0.0])
    thrust = np.zeros(3)
    mass = 1000.0
    
    deriv = compute_derivatives(0.0, state, thrust, mass, gravity=GRAVITY_MOON)
    az = deriv[5]
    
    assert pytest.approx(az, abs=1e-5) == -GRAVITY_MOON

def test_constant_thrust():
    """
    Test 2 - Constant Thrust
    Verify acceleration follows a = (T - mg)/m
    """
    state = np.array([0.0, 0.0, 1000.0, 0.0, 0.0, 0.0])
    mass = 1000.0
    T_mag = 2000.0 # Upward thrust in N
    thrust = np.array([0.0, 0.0, T_mag])
    
    expected_a = (T_mag - mass * GRAVITY_MOON) / mass
    
    deriv = compute_derivatives(0.0, state, thrust, mass, gravity=GRAVITY_MOON)
    az = deriv[5]
    
    assert pytest.approx(az, abs=1e-5) == expected_a

def test_hover_thrust():
    """
    Test 3 - Hover-equivalent Thrust
    T = mg. Expected vertical acceleration = 0
    """
    state = np.array([0.0, 0.0, 1000.0, 0.0, 0.0, 0.0])
    mass = 1000.0
    thrust = np.array([0.0, 0.0, mass * GRAVITY_MOON])
    
    deriv = compute_derivatives(0.0, state, thrust, mass, gravity=GRAVITY_MOON)
    az = deriv[5]
    
    assert pytest.approx(az, abs=1e-5) == 0.0

def test_controlled_descent():
    """
    Test 4 - Controlled Descent
    Start from configurable altitude. Apply a controlled thrust profile.
    Verify altitude decreases and velocity is controlled.
    """
    initial_z = 100.0
    initial_state = np.array([0.0, 0.0, initial_z, 0.0, 0.0, 0.0])
    mass = 1000.0
    
    # Very basic proportional descent controller for testing
    def pd_thrust_profile(t, state):
        z = state[2]
        vz = state[5]
        
        # Target z = 0, target vz = -1.0
        # If z is large, we want vz = -2.0. As z -> 0, vz -> -0.5
        target_vz = -1.0
        
        # Error in velocity
        error_vz = target_vz - vz
        
        # PD command for acceleration
        a_cmd = 0.5 * error_vz
        
        # Add gravity compensation
        Fz = mass * (a_cmd + GRAVITY_MOON)
        
        # Saturate thrust
        thrust = np.array([0.0, 0.0, Fz])
        return saturate_thrust(thrust, max_thrust=3000.0)
    
    sol = simulate(
        initial_state, 
        mass, 
        pd_thrust_profile, 
        duration_s=20.0, 
        max_step=0.5
    )
    
    final_z = sol.y[2, -1]
    final_vz = sol.y[5, -1]
    
    # Assert altitude decreased
    assert final_z < initial_z
    
    # Assert vertical velocity was controlled (near our target of -1.0 m/s)
    assert pytest.approx(final_vz, abs=0.5) == -1.0
