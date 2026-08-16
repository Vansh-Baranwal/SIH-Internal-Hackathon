"""
M5 -> M6 Boundary Adapter

Translates M5's site evaluation output (recommended and rejected sites)
into M6's strictly defined Pydantic schemas (SiteResult) for use in
reachability, trajectory generation, and replanning.
"""

from typing import List, Dict, Any
from lunar_hazard_mapper.m6_planner.schemas import SiteResult, LanderProfile


def convert_m5_sites_to_m6_results(m5_evaluation_result: Dict[str, Any]) -> List[SiteResult]:
    """
    Translates M5's evaluation payload into M6 SiteResult schemas.
    
    Mapping explicitly:
    - M5 site_id / rank -> M6 SiteResult.siteId
    - M5 x_m            -> M6 SiteResult.x
    - M5 y_m            -> M6 SiteResult.y
    - M5 score          -> M6 SiteResult.score
    - M5 zone_summary   -> M6 SiteResult.metrics
    - M5 footprint_summary -> M6 SiteResult.metrics
    
    Args:
        m5_evaluation_result: The dictionary returned by M5's evaluate_sites().
        
    Returns:
        List of M6 SiteResult objects (both recommended and rejected).
    """
    m6_results = []
    
    # Process recommended (feasible) sites
    for site in m5_evaluation_result.get("recommended_sites", []):
        m6_results.append(
            SiteResult(
                siteId=str(site.get("site_id", f"SITE_RANK_{site.get('rank', 0)}")),
                x=float(site["x_m"]),
                y=float(site["y_m"]),
                score=float(site["score"]),
                feasible=True,
                reasons=[],
                metrics={
                    "zone_summary": site.get("zone_summary", {}),
                    "footprint_summary": site.get("footprint_summary", {}),
                    "rank": site.get("rank"),
                    "row": site.get("row"),
                    "col": site.get("col")
                }
            )
        )
        
    # Process rejected (infeasible) sites (if needed by downstream tracking)
    for site in m5_evaluation_result.get("rejected_sites", []):
        m6_results.append(
            SiteResult(
                siteId=str(site.get("site_id", "REJECTED")),
                x=float(site.get("x_m", 0.0)),
                y=float(site.get("y_m", 0.0)),
                score=0.0,
                feasible=False,
                reasons=[str(site.get("reason", "Unknown failure"))],
                metrics={
                    "violations": site.get("violations", []),
                    "row": site.get("row"),
                    "col": site.get("col")
                }
            )
        )
        
    return m6_results


def convert_m5_lander_to_m6_profile(m5_lander: Dict[str, Any]) -> LanderProfile:
    """
    Converts M5's simplified lander summary into M6's LanderProfile model.
    Since M5 focuses on safety/terrain constraints, it may omit dynamic physics
    parameters. We use reasonable defaults for any missing M6 physics fields to
    allow the 3-DOF engine to run.
    """
    return LanderProfile(
        name=m5_lander.get("name", "Unknown Lander"),
        mass=float(m5_lander.get("mass_kg", 1500.0)),
        maxSlope=float(m5_lander.get("max_slope_deg", 10.0)),
        maxVz=float(m5_lander.get("max_vz_mps", -3.0)),  # Missing from M5, default -3.0
        maxVxy=float(m5_lander.get("max_vxy_mps", 1.5)), # Missing from M5, default 1.5
        footprint=float(m5_lander.get("footprint_radius_m", 3.5)),
        clearance=float(m5_lander.get("min_clearance_m", 0.5)),
        deltaVBudget=float(m5_lander.get("delta_v_budget_mps", 500.0)), # Missing, default 500.0
        maxThrust=float(m5_lander.get("max_thrust_n", 3000.0)),         # Missing, default 3000.0
        isp=float(m5_lander.get("isp_s", 311.0)),
        maxTiltAngle=float(m5_lander.get("max_tilt_deg", 45.0)),
        uncertaintyLimit=float(m5_lander.get("uncertainty_limit", 0.9))
    )
