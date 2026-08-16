from typing import Tuple, List
from lunar_hazard_mapper.m6_planner.schemas import Trajectory, LanderProfile

def validate_touchdown(trajectory: Trajectory, lander: LanderProfile, target_x: float, target_y: float) -> Tuple[bool, List[str]]:
    """
    Evaluates whether the final state of the trajectory meets the lander's touchdown constraints.
    
    Args:
        trajectory: The generated trajectory.
        lander: LanderProfile containing maximum limits.
        target_x: Target site X coordinate (for distance error).
        target_y: Target site Y coordinate.
        
    Returns:
        (success, [list of rejection reasons])
    """
    reasons = []
    success = True
    
    final_state = trajectory.finalState
    
    # 1. Vertical velocity constraint
    # maxVz is typically negative (e.g. -3.0). vz must be >= maxVz.
    # Note: vz is negative on descent. 
    # E.g. vz = -4.0 is faster than limit -3.0.
    if final_state.vz < lander.maxVz:
        success = False
        reasons.append(f"Touchdown vertical velocity exceeded: {final_state.vz:.2f} m/s < limit {lander.maxVz:.2f} m/s")
        
    # 2. Horizontal velocity constraint
    vxy = (final_state.vx**2 + final_state.vy**2)**0.5
    if vxy > lander.maxVxy:
        success = False
        reasons.append(f"Touchdown horizontal velocity exceeded: {vxy:.2f} m/s > limit {lander.maxVxy:.2f} m/s")
        
    # 3. Targeting error (must land within reasonable radius of target, say 5 meters for baseline)
    distance_error = ((final_state.x - target_x)**2 + (final_state.y - target_y)**2)**0.5
    TARGET_RADIUS_LIMIT = 5.0
    if distance_error > TARGET_RADIUS_LIMIT:
        success = False
        reasons.append(f"Targeting distance error exceeded: {distance_error:.2f} m > limit {TARGET_RADIUS_LIMIT:.2f} m")
        
    return success, reasons
