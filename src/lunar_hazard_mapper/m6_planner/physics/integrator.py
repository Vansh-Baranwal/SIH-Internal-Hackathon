import numpy as np
from scipy.integrate import solve_ivp
from typing import Callable, Tuple, Any
from lunar_hazard_mapper.m6_planner.physics.dynamics import compute_derivatives
from lunar_hazard_mapper.m6_planner.physics.constants import GRAVITY_MOON

from lunar_hazard_mapper.m6_planner.adapters.terrain_provider import TerrainProvider, MockTerrainProvider

def simulate(
    initial_state_vector: np.ndarray, 
    mass: float,
    thrust_profile_func: Callable[[float, np.ndarray], np.ndarray], 
    duration_s: float, 
    terrain_provider: TerrainProvider = None,
    max_step: float = 0.1,
    gravity: float = GRAVITY_MOON
) -> Any:
    """
    Numerically integrates the 3-DOF lunar lander dynamics over a given duration.
    
    Args:
        initial_state_vector: [x, y, z, vx, vy, vz]
        mass: Mass of the lander (kg). Treated as constant in this basic model, 
              though a full model would update mass via thrust_profile_func.
        thrust_profile_func: A callable that takes (t, state) and returns thrust vector [Tx, Ty, Tz]
        duration_s: Total simulation time in seconds.
        terrain_provider: Provider to compute dynamic ground collision threshold.
        max_step: Maximum integration step size.
        gravity: Gravity magnitude in m/s^2.
        
    Returns:
        solution: SciPy OdeResult object containing t, y, status, and t_events.
    """
    if terrain_provider is None:
        terrain_provider = MockTerrainProvider(0.0)
        
    def ode_system(t: float, y: np.ndarray) -> np.ndarray:
        # Get thrust vector from the controller/profile
        thrust = thrust_profile_func(t, y)
        return compute_derivatives(t, y, thrust, mass, gravity)
        
    def ground_event(t: float, y: np.ndarray) -> float:
        """
        Event function to detect when lander altitude drops below terrain height.
        """
        x, y_pos, z = y[0], y[1], y[2]
        terrain_z = terrain_provider.get_height(x, y_pos)
        return z - terrain_z
        
    ground_event.terminal = True
    ground_event.direction = -1 # Trigger only when descending through the boundary
    
    # Run SciPy solve_ivp
    solution = solve_ivp(
        fun=ode_system,
        t_span=(0.0, duration_s),
        y0=initial_state_vector,
        max_step=max_step,
        method='RK45',
        events=[ground_event]
    )
    
    return solution
