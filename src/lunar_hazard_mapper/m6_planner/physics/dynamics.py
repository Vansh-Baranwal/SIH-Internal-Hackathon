import numpy as np
from lunar_hazard_mapper.m6_planner.physics.constants import GRAVITY_MOON

def compute_derivatives(t: float, state_vector: np.ndarray, thrust_vector: np.ndarray, mass: float, gravity: float = GRAVITY_MOON) -> np.ndarray:
    """
    Computes the derivatives of the state vector for 3-DOF translational dynamics.
    
    Args:
        t: Current simulation time (s)
        state_vector: Array [x, y, z, vx, vy, vz]
        thrust_vector: Applied thrust force vector [Tx, Ty, Tz] in Newtons
        mass: Current lander mass in kg
        gravity: Gravity acceleration magnitude in m/s^2 (downward Z)
        
    Returns:
        Derivatives array [vx, vy, vz, ax, ay, az]
    """
    # Unpack state
    x, y, z, vx, vy, vz = state_vector
    
    # Gravitational force vector (downward in local Z)
    F_gravity = np.array([0.0, 0.0, -mass * gravity])
    
    # Net force F_net = F_thrust + F_gravity
    F_net = thrust_vector + F_gravity
    
    # Acceleration a = F_net / m
    ax, ay, az = F_net / mass
    
    # Return derivative [dx/dt, dy/dt, dz/dt, dvx/dt, dvy/dt, dvz/dt]
    return np.array([vx, vy, vz, ax, ay, az])
