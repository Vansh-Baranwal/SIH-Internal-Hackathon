from dataclasses import dataclass
from typing import Optional, List

@dataclass
class PhysicsState:
    """
    Canonical representation of the lander's 3-DOF translational physics state.
    Used consistently across physics, trajectory generation, and controllers.
    
    Coordinates are in the local Cartesian frame:
    x = East (m)
    y = North (m)
    z = Up (m)
    """
    t: float        # Time (s)
    x: float        # Position X (m)
    y: float        # Position Y (m)
    z: float        # Position Z (m)
    vx: float       # Velocity X (m/s)
    vy: float       # Velocity Y (m/s)
    vz: float       # Velocity Z (m/s)
    mass: float     # Current mass (kg)
    
    # Optional fields for logging or advanced control
    ax: float = 0.0
    ay: float = 0.0
    az: float = 0.0
    
    attitude: Optional[List[float]] = None

    def position(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)
        
    def velocity(self) -> tuple[float, float, float]:
        return (self.vx, self.vy, self.vz)
