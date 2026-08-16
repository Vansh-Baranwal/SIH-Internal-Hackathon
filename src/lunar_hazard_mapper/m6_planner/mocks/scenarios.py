from typing import Dict, Any, List
from lunar_hazard_mapper.m6_planner.mocks.m3_mock import MockM3Provider
from lunar_hazard_mapper.m6_planner.mocks.m4_mock import MockM4Provider
from lunar_hazard_mapper.m6_planner.schemas import LanderProfile, SiteResult

# Predefined deterministic scenarios for reliable testing and demos
class PredefinedScenarios:
    SCENARIO_NORMAL = "SCENARIO_NORMAL"
    SCENARIO_HAZARD_REPLAN = "SCENARIO_HAZARD_REPLAN"
    SCENARIO_NO_REACHABLE_SITE = "SCENARIO_NO_REACHABLE_SITE"
    SCENARIO_LOW_CONFIDENCE = "SCENARIO_LOW_CONFIDENCE"
    SCENARIO_MULTI_LANDER = "SCENARIO_MULTI_LANDER"

def get_scenario_sites(scenario_name: str) -> List[SiteResult]:
    """
    Returns predefined deterministic candidate sites based on the requested scenario.
    """
    if scenario_name == PredefinedScenarios.SCENARIO_HAZARD_REPLAN:
        return [
            # Site A (Primary target initially, will be invalidated by hazard injection)
            SiteResult(
                siteId="SITE_A", x=100.0, y=100.0, score=0.98, feasible=True, 
                reasons=[], metrics={"slope": 2.1, "distance": 141.4}
            ),
            # Site B (Safe, reachable, next best alternative)
            SiteResult(
                siteId="SITE_B", x=-50.0, y=80.0, score=0.85, feasible=True, 
                reasons=[], metrics={"slope": 5.4, "distance": 94.3}
            ),
            # Site C (Safe but unreachable due to distance/delta-V)
            SiteResult(
                siteId="SITE_C", x=3000.0, y=4000.0, score=0.95, feasible=True, 
                reasons=[], metrics={"slope": 3.0, "distance": 5000.0}
            ),
            # Site D (Unsafe/Infeasible)
            SiteResult(
                siteId="SITE_D", x=20.0, y=-20.0, score=0.20, feasible=False, 
                reasons=["Slope exceeds 12 deg"], metrics={"slope": 14.5, "distance": 28.2}
            )
        ]
    elif scenario_name == PredefinedScenarios.SCENARIO_NO_REACHABLE_SITE:
        return [
            # All sites are either infeasible or too far away
            SiteResult(
                siteId="SITE_A", x=3000.0, y=4000.0, score=0.95, feasible=True, 
                reasons=[], metrics={"slope": 3.0, "distance": 5000.0}
            ),
            SiteResult(
                siteId="SITE_B", x=10.0, y=10.0, score=0.10, feasible=False, 
                reasons=["Crater boundary"], metrics={"slope": 25.0, "distance": 14.1}
            )
        ]
    
    # Default (SCENARIO_NORMAL)
    return [
        SiteResult(
            siteId="SITE_PRIMARY", x=50.0, y=50.0, score=0.99, feasible=True, 
            reasons=[], metrics={"slope": 1.0, "distance": 70.7}
        )
    ]

def build_standalone_demo_scenario(scenario_name: str = PredefinedScenarios.SCENARIO_HAZARD_REPLAN) -> Dict[str, Any]:
    """
    Constructs a complete suite of mock inputs representing a predefined deterministic scenario.
    """
    # Fix the seeds so that the background DEM/Hazard arrays are always identical
    m3 = MockM3Provider(seed=42)
    m4 = MockM4Provider(seed=42)
    
    dem = m3.generate_synthetic_dem(width=200, height=200, resolution=5.0)
    hazards = m4.generate_hazard_map(width=200, height=200)
    
    lander = LanderProfile(
        name="Mock Hero Lander",
        mass=1500.0,
        maxSlope=12.0,
        maxVz=-3.0,
        maxVxy=1.5,
        footprint=3.5,
        clearance=0.8,
        deltaVBudget=500.0,
        maxThrust=3000.0,
        isp=311.0,
        maxTiltAngle=45.0
    )
    
    # Maneuver Config
    # Default maneuver parameters for the demo
    # (Uncertainty limit is generally a mission constraint)
    # The schemas expect it somewhere, so we'll just mock it.
    
    candidates = get_scenario_sites(scenario_name)
    
    return {
        "dem": dem,
        "hazards": hazards,
        "lander": lander,
        "candidates": candidates
    }
