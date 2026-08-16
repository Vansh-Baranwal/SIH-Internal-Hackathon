import numpy as np
from typing import Callable, Dict, Any, List
from lunar_hazard_mapper.m6_planner.schemas import Trajectory, TrajectoryPoint, TrajectoryStatus, LanderProfile, ManeuverConfig
from lunar_hazard_mapper.m6_planner.physics.integrator import simulate
from lunar_hazard_mapper.m6_planner.physics.constants import GRAVITY_MOON
from lunar_hazard_mapper.m6_planner.physics.thrust import saturate_thrust
from lunar_hazard_mapper.m6_planner.adapters.terrain_provider import TerrainProvider

def generate_trajectory(
    initial_state: np.ndarray, 
    target_pos: np.ndarray, 
    lander: LanderProfile,
    target_site_id: str,
    maneuver_config: ManeuverConfig = None,
    terrain_provider: TerrainProvider = None
) -> Trajectory:
    """
    Generates a physically meaningful trajectory using a baseline PD controller.
    
    Args:
        initial_state: [x, y, z, vx, vy, vz]
        target_pos: [x, y, z] of the target site
        lander: Lander physical profile
        target_site_id: Identifier for the target site
        maneuver_config: Constraints like max duration
        terrain_provider: Optional terrain provider for collision detection
        
    Returns:
        Trajectory schema object.
    """
    if maneuver_config is None:
        maneuver_config = ManeuverConfig()
        
    # PD Controller gains (configurable research baseline)
    Kp_xy = 0.5
    Kd_xy = 1.0
    Kp_z = 0.2
    Kd_z = 0.8
    
    def thrust_controller(t: float, state: np.ndarray) -> np.ndarray:
        pos = state[0:3]
        vel = state[3:6]
        
        # 1. Position error
        pos_error = target_pos - pos
        
        # 2. Velocity error (target velocity is 0 at the target site)
        # Note: A real landing profile would have a non-zero target velocity during descent,
        # but for this baseline, we aim for 0 velocity at the target.
        target_vel = np.array([0.0, 0.0, -1.0]) if pos_error[2] > 10.0 else np.zeros(3)
        vel_error = target_vel - vel
        
        # 3. PD controller -> Desired acceleration
        a_cmd_x = Kp_xy * pos_error[0] + Kd_xy * vel_error[0]
        a_cmd_y = Kp_xy * pos_error[1] + Kd_xy * vel_error[1]
        a_cmd_z = Kp_z * pos_error[2] + Kd_z * vel_error[2]
        
        a_cmd = np.array([a_cmd_x, a_cmd_y, a_cmd_z])
        
        # 4. Thrust command (compensating for gravity)
        gravity_comp = np.array([0.0, 0.0, GRAVITY_MOON])
        thrust_cmd = lander.mass * (a_cmd + gravity_comp)
        
        # 5. Thrust saturation and tilt constraint
        return saturate_thrust(thrust_cmd, lander.maxThrust, lander.maxTiltAngle)

    # 6. Integrate dynamics (Physics engine)
    sol = simulate(
        initial_state_vector=initial_state,
        mass=lander.mass,
        thrust_profile_func=thrust_controller,
        duration_s=maneuver_config.maxDuration,
        terrain_provider=terrain_provider,
        max_step=0.5
    )
    
    t_vals = sol.t
    states = sol.y
    
    # Evaluate Trajectory Status
    status = TrajectoryStatus.IN_PROGRESS
    
    if sol.status == 1:
        # A terminal event occurred (ground contact)
        final_pos = states[0:3, -1]
        final_vel = states[3:6, -1]
        
        # Check if we are near the target
        dist_to_target = np.linalg.norm(final_pos[0:2] - target_pos[0:2])
        vz_ok = final_vel[2] >= lander.maxVz # maxVz is negative, so greater means slower (e.g., -1.5 >= -2.0)
        vxy_ok = np.linalg.norm(final_vel[0:2]) <= lander.maxVxy
        
        if dist_to_target < lander.footprint * 5.0 and vz_ok and vxy_ok:
            status = TrajectoryStatus.SUCCESS
        else:
            status = TrajectoryStatus.GROUND_COLLISION
    elif sol.status == 0:
        # Reached the end of integration time without hitting ground
        status = TrajectoryStatus.TIMEOUT
    else:
        status = TrajectoryStatus.INVALID
    
    # 7. Package into Trajectory schema
    points: List[TrajectoryPoint] = []
    for i in range(len(t_vals)):
        pt = TrajectoryPoint(
            t=float(t_vals[i]),
            x=float(states[0, i]),
            y=float(states[1, i]),
            z=float(states[2, i]),
            vx=float(states[3, i]),
            vy=float(states[4, i]),
            vz=float(states[5, i]),
            attitude=None
        )
        points.append(pt)
        
    metadata = {
        "controller": "Baseline PD",
        "duration_s": maneuver_config.maxDuration,
        "status_code": sol.status
    }
        
    return Trajectory(
        targetSiteId=target_site_id,
        status=status,
        points=points,
        initialState=points[0],
        finalState=points[-1],
        metadata=metadata
    )
