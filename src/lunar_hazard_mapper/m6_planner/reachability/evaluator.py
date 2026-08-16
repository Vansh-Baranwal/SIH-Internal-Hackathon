from typing import Tuple, List, Optional
import numpy as np
from lunar_hazard_mapper.m6_planner.schemas import SiteResult, LanderProfile, ManeuverConfig
from lunar_hazard_mapper.m6_planner.reachability.delta_v import get_available_delta_v, estimate_required_delta_v

def evaluate_reachability(
    site: SiteResult, 
    lander: LanderProfile, 
    current_state: np.ndarray, 
    config: ManeuverConfig = None
) -> Tuple[bool, float, Optional[str]]:
    """
    Evaluates if a candidate site is reachable given current state and lander budget.
    
    Args:
        site: Candidate SiteResult
        lander: LanderProfile
        current_state: [x, y, z, vx, vy, vz]
        config: ManeuverConfig for delta-v limits
        
    Returns:
        (is_reachable, maneuver_cost, rejection_reason)
    """
    if config is None:
        config = ManeuverConfig()
        
    if not site.feasible:
        return False, 0.0, "Site already marked infeasible by M5"
        
    current_pos = current_state[:3]
    current_vel = current_state[3:]
    target_pos = np.array([site.x, site.y, 0.0])
    
    available_dv = get_available_delta_v(lander)
    required_dv = estimate_required_delta_v(current_pos, current_vel, target_pos, config)
    
    # Store the maneuver cost in the site metrics
    if site.metrics is None:
        site.metrics = {}
    site.metrics["maneuverCost"] = required_dv
    
    if required_dv == float('inf'):
        return False, required_dv, "Maneuver mathematically infeasible (insufficient time/distance ratio)"
        
    if required_dv > available_dv:
        return False, required_dv, f"Required Delta-V ({required_dv:.1f} m/s) exceeds budget ({available_dv:.1f} m/s)"
        
    return True, required_dv, None

def filter_reachable_sites(
    candidates: List[SiteResult], 
    lander: LanderProfile, 
    current_state: np.ndarray,
    config: ManeuverConfig = None
) -> Tuple[List[SiteResult], List[SiteResult]]:
    """
    Splits candidates into reachable and unreachable lists.
    
    Returns:
        (reachable_sites, unreachable_sites)
    """
    if config is None:
        config = ManeuverConfig()
        
    reachable = []
    unreachable = []
    
    for site in candidates:
        is_reachable, cost, reason = evaluate_reachability(site, lander, current_state, config)
        if is_reachable:
            reachable.append(site)
        else:
            site.feasible = False
            if reason not in site.reasons:
                site.reasons.append(reason)
            unreachable.append(site)
            
    return reachable, unreachable
