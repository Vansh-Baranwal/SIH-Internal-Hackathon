import numpy as np
from typing import Callable

def saturate_thrust(thrust_vector: np.ndarray, max_thrust: float, max_tilt_angle_deg: float = 45.0) -> np.ndarray:
    """
    Clips the requested thrust vector magnitude so it does not exceed max_thrust,
    and enforces a maximum tilt angle relative to the vertical Z axis.
    
    Args:
        thrust_vector: Requested thrust [Tx, Ty, Tz]
        max_thrust: Maximum possible thrust magnitude in Newtons
        max_tilt_angle_deg: Maximum tilt from vertical in degrees
        
    Returns:
        Constrained thrust vector [Tx, Ty, Tz]
    """
    tx, ty, tz = thrust_vector
    
    # 1. Enforce Tilt Constraint
    # A lander cannot point its thrust vector fully horizontally. 
    # Thrust Z must be non-negative for this constraint.
    if tz <= 0:
        # If requested thrust is downward or zero, force it to zero lateral
        # (Though usually a lander can't thrust downwards anyway)
        tz = max(tz, 0.0)
        tx, ty = 0.0, 0.0
    else:
        th = np.sqrt(tx**2 + ty**2)
        import math
        max_tilt_rad = math.radians(max_tilt_angle_deg)
        max_th = tz * math.tan(max_tilt_rad)
        
        if th > max_th:
            # Scale tx and ty down to match max_th
            scale = max_th / th
            tx *= scale
            ty *= scale
            
    constrained_thrust = np.array([tx, ty, tz])
    
    # 2. Enforce Magnitude Constraint
    magnitude = np.linalg.norm(constrained_thrust)
    if magnitude > max_thrust:
        constrained_thrust *= (max_thrust / magnitude)
        
    return constrained_thrust

def get_constant_thrust_profile(thrust_vector: np.ndarray) -> Callable[[float, np.ndarray], np.ndarray]:
    """
    Returns a constant thrust profile function for testing.
    """
    return lambda t, y: thrust_vector

def get_zero_thrust_profile() -> Callable[[float, np.ndarray], np.ndarray]:
    """
    Returns a zero thrust profile function (free fall).
    """
    return lambda t, y: np.zeros(3)
