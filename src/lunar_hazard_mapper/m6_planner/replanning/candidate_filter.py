from typing import List, Tuple
import numpy as np
from lunar_hazard_mapper.m6_planner.schemas import SiteResult, LanderProfile, ManeuverConfig
from lunar_hazard_mapper.m6_planner.reachability.evaluator import evaluate_reachability

def get_viable_alternatives(
    candidates: List[SiteResult], 
    invalidated_target_id: str, 
    lander: LanderProfile, 
    current_state: np.ndarray,
    maneuver_config: ManeuverConfig = None
) -> Tuple[List[SiteResult], List[SiteResult]]:
    """
    Filters candidates to find viable alternatives for re-planning.
    A viable alternative must be:
    1. Not the currently invalidated target.
    2. Marked feasible by M5.
    3. Reachable from the current state given delta-V constraints.
    
    Returns:
        (viable_candidates, rejected_candidates)
    """
    if maneuver_config is None:
        maneuver_config = ManeuverConfig()
        
    viable = []
    rejected = []
    
    for site in candidates:
        if site.siteId == invalidated_target_id:
            site.feasible = False
            if "Invalidated by hazard event" not in site.reasons:
                site.reasons.append("Invalidated by hazard event")
            rejected.append(site)
            continue
            
        if not site.feasible:
            rejected.append(site)
            continue
            
        is_reachable, cost, reason = evaluate_reachability(site, lander, current_state, maneuver_config)
        
        if is_reachable:
            viable.append(site)
        else:
            site.feasible = False
            if reason not in site.reasons:
                site.reasons.append(reason)
            rejected.append(site)
            
    return viable, rejected
