import numpy as np
from typing import List, Dict, Any
from lunar_hazard_mapper.m6_planner.schemas import Trajectory, LanderProfile, UncertaintyConfig, ManeuverConfig
from lunar_hazard_mapper.m6_planner.uncertainty.noise import apply_sensor_noise
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
from lunar_hazard_mapper.m6_planner.trajectory.constraints import validate_touchdown
from lunar_hazard_mapper.m6_planner.adapters.terrain_provider import MockTerrainProvider

def run_monte_carlo_simulations(
    initial_state_mean: np.ndarray,
    target_pos: np.ndarray,
    lander: LanderProfile,
    target_site_id: str,
    num_runs: int = 50,
    uncertainty_config: UncertaintyConfig = None,
    maneuver_config: ManeuverConfig = None
) -> Dict[str, Any]:
    """
    Runs a Monte Carlo simulation of the trajectory generation subject to initial state uncertainty.
    
    Args:
        initial_state_mean: The mean starting state [x, y, z, vx, vy, vz]
        target_pos: Target [x, y, z]
        lander: LanderProfile
        target_site_id: Site identifier
        num_runs: Number of simulations to execute
        uncertainty_config: Config for noise standard deviations
        maneuver_config: Config for trajectory constraints
        
    Returns:
        Dictionary of uncertainty metrics.
    """
    if uncertainty_config is None:
        uncertainty_config = UncertaintyConfig()
        
    if maneuver_config is None:
        maneuver_config = ManeuverConfig()
        
    rng = np.random.default_rng(uncertainty_config.seed)
    terrain_provider = MockTerrainProvider(0.0)
    
    success_count = 0
    final_errors = []
    
    for i in range(num_runs):
        # 1. Perturb initial state
        run_seed = int(rng.integers(0, 1000000))
        noisy_initial_state = apply_sensor_noise(
            initial_state_mean, 
            config=uncertainty_config,
            seed=run_seed
        )
        
        # 2. Generate trajectory
        trajectory = generate_trajectory(
            initial_state=noisy_initial_state,
            target_pos=target_pos,
            lander=lander,
            target_site_id=target_site_id,
            maneuver_config=maneuver_config,
            terrain_provider=terrain_provider
        )
        
        # 3. Validate touchdown
        success, _ = validate_touchdown(trajectory, lander, target_x=target_pos[0], target_y=target_pos[1])
        
        if success:
            success_count += 1
            
        # Record final horizontal targeting error
        fx, fy = trajectory.finalState.x, trajectory.finalState.y
        error_dist = ((fx - target_pos[0])**2 + (fy - target_pos[1])**2)**0.5
        final_errors.append(error_dist)
        
    # Compile metrics
    success_rate = success_count / num_runs if num_runs > 0 else 0.0
    mean_error = float(np.mean(final_errors)) if final_errors else 0.0
    std_error = float(np.std(final_errors)) if final_errors else 0.0
    
    return {
        "success_rate": success_rate,
        "landing_error_mean": mean_error,
        "landing_error_std": std_error,
        "num_runs": num_runs
    }
