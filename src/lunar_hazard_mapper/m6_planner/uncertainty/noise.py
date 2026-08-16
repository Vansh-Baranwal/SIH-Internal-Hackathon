import numpy as np
from lunar_hazard_mapper.m6_planner.schemas import UncertaintyConfig

def apply_sensor_noise(state: np.ndarray, config: UncertaintyConfig = None, seed: int = None) -> np.ndarray:
    """
    Applies Gaussian noise to the state vector representing sensor uncertainty.
    
    Args:
        state: [x, y, z, vx, vy, vz]
        config: Configuration containing std devs
        seed: Random seed for repeatability (overrides config.seed if provided)
        
    Returns:
        Noisy state vector.
    """
    if config is None:
        config = UncertaintyConfig()
        
    use_seed = seed if seed is not None else config.seed
    rng = np.random.default_rng(use_seed)
    noisy_state = state.copy()
    
    # Position noise
    noisy_state[0:2] += rng.normal(0, config.position_std_m, 2)
    noisy_state[2] += rng.normal(0, config.altitude_std_m) # Z might have different sensor (e.g. radar vs camera)
    
    # Velocity noise
    noisy_state[3:6] += rng.normal(0, config.velocity_std_mps, 3)
    
    return noisy_state
