from typing import Optional
from lunar_hazard_mapper.m6_planner.schemas import SiteResult, LanderProfile
from lunar_hazard_mapper.m6_planner.coordinate import CoordinateTransform

class SiteEvaluatorAdapter:
    """
    Adapter bridging frontend interactions (world coordinates) to M5's site evaluation logic.
    M6 does not evaluate slope/crater/boulders; it delegates this to M5 via this interface.
    """
    
    def __init__(self, coordinate_transform: CoordinateTransform):
        self.transform = coordinate_transform

    def evaluate_interaction(self, wx: float, wy: float, wz: float, lander: LanderProfile, site_id: str = "CLICKED_SITE") -> SiteResult:
        """
        Takes a world coordinate from a frontend interaction, transforms it to the 
        local simulation coordinate frame, and queries the M5 evaluator.
        
        Args:
            wx: World X coordinate
            wy: World Y coordinate
            wz: World Z coordinate
            lander: The current lander profile
            site_id: Identifier for the generated site
            
        Returns:
            SiteResult containing the safety/feasibility evaluated by M5.
        """
        # 1. Transform world coordinates to Local simulation coordinates
        local_x, local_y, local_z = self.transform.world_to_local(wx, wy, wz)
        
        # 2. Call M5 internal evaluator (Mocked for now)
        return self._call_m5_evaluator(local_x, local_y, lander, site_id)
        
    def _call_m5_evaluator(self, local_x: float, local_y: float, lander: LanderProfile, site_id: str) -> SiteResult:
        """
        Internal delegation to M5 module.
        Currently a placeholder mock implementation until M5 is integrated.
        """
        # MOCK M5 BEHAVIOR
        # Assume any click within 500m of origin is safe for demo purposes
        distance_sq = local_x**2 + local_y**2
        feasible = distance_sq <= 500**2
        
        reasons = []
        if not feasible:
            reasons.append("Mock M5: Site too far from origin (hazard simulated).")
            
        return SiteResult(
            siteId=site_id,
            x=local_x,
            y=local_y,
            score=0.9 if feasible else 0.2,
            feasible=feasible,
            reasons=reasons,
            metrics={"slope": 5.0, "mock": True}
        )
