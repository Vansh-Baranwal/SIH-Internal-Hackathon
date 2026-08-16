from typing import List, Optional
from dataclasses import dataclass
from lunar_hazard_mapper.m6_planner.schemas import SiteResult

@dataclass
class RankingWeights:
    terrain_risk: float = 1.0
    uncertainty: float = 1.0
    delta_v_cost: float = 1.0
    distance: float = 1.0

def rank_candidates(candidates: List[SiteResult], weights: RankingWeights = RankingWeights()) -> List[SiteResult]:
    """
    Ranks a list of candidate sites based on a cost function combining:
    - terrain risk (from M5 safety score)
    - uncertainty (if provided in metrics)
    - maneuver/Δv cost (if computed/provided)
    - distance (if provided)
    
    Returns a sorted list of candidates, where the first element is the best (lowest cost).
    """
    def calculate_cost(site: SiteResult) -> float:
        # Lower score is worse, so risk = 1.0 - score
        risk = 1.0 - site.score
        
        # Pull optional metrics if available
        uncertainty = site.metrics.get("uncertainty", 0.0)
        dv_cost = site.metrics.get("maneuverCost", 0.0)
        distance = site.metrics.get("distance", 0.0)
        
        total_cost = (
            weights.terrain_risk * risk +
            weights.uncertainty * uncertainty +
            weights.delta_v_cost * dv_cost +
            weights.distance * distance
        )
        return total_cost

    # Sort candidates by calculated cost
    sorted_candidates = sorted(candidates, key=calculate_cost)
    return sorted_candidates

def select_best_candidate(candidates: List[SiteResult], weights: RankingWeights = RankingWeights()) -> Optional[SiteResult]:
    """
    Selects the single best candidate from the list.
    """
    if not candidates:
        return None
    
    ranked = rank_candidates(candidates, weights)
    return ranked[0]
