from lunar_hazard_mapper.m6_planner.schemas import LanderProfile, ManeuverConfig
from lunar_hazard_mapper.m6_planner.physics.constants import GRAVITY_MOON
import numpy as np

def get_available_delta_v(lander: LanderProfile) -> float:
    """
    Returns the total remaining Delta-V budget available for the lander.
    """
    return lander.deltaVBudget

def estimate_required_delta_v(current_pos: np.ndarray, current_vel: np.ndarray, target_pos: np.ndarray, config: ManeuverConfig = None) -> float:
    """
    Estimates the required Delta-V to reach the target site and land softly.
    Uses a rough approximation based on kinematics and gravity losses.
    
    Args:
        current_pos: [x, y, z]
        current_vel: [vx, vy, vz]
        target_pos: [x, y, z]
        config: ManeuverConfig with time and safety margin
        
    Returns:
        Estimated delta-v cost in m/s
    """
    if config is None:
        config = ManeuverConfig()
        
    time_to_target = config.maneuverTime
    
    # 1. Reject physically invalid or excessively short maneuver times
    minimum_valid_time = 1.0 # 1 second minimum to prevent divide by zero and absurd accelerations
    if time_to_target <= minimum_valid_time:
        return float('inf')
        
    # 2. Delta-V to kill current velocity
    dv_kinematic = np.linalg.norm(current_vel)
    
    # 3. Delta-V required to move to target horizontally
    dist_xy = np.linalg.norm(target_pos[:2] - current_pos[:2])
    
    # Very rough estimate: accelerate to half distance, decelerate rest of the way
    v_peak = 2.0 * (dist_xy / time_to_target)
    dv_horizontal = 2.0 * v_peak  # accel + decel
        
    # 4. Gravity losses (engine must fight gravity for the duration of the maneuver)
    dv_gravity_loss = GRAVITY_MOON * time_to_target
    
    total_dv = (dv_kinematic + dv_horizontal + dv_gravity_loss) * config.safetyMargin
    
    return float(total_dv)
