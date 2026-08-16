import pytest
from lunar_hazard_mapper.m6_planner.schemas import SiteResult
from lunar_hazard_mapper.m6_planner.replanning.ranking import rank_candidates, select_best_candidate, RankingWeights

def test_site_ranking():
    candidates = [
        # Site A: Very safe, but far (high distance cost)
        SiteResult(siteId="A", x=1000.0, y=1000.0, score=0.99, feasible=True, reasons=[], metrics={"distance": 1414.0}),
        # Site B: Less safe, but very close
        SiteResult(siteId="B", x=10.0, y=10.0, score=0.80, feasible=True, reasons=[], metrics={"distance": 14.1})
    ]
    
    # If we weight distance heavily, B should win
    weights_dist = RankingWeights(terrain_risk=1.0, distance=10.0)
    best_dist = select_best_candidate(candidates, weights_dist)
    assert best_dist.siteId == "B"
    
    # If we weight risk heavily, A should win
    weights_risk = RankingWeights(terrain_risk=10000.0, distance=1.0)
    best_risk = select_best_candidate(candidates, weights_risk)
    assert best_risk.siteId == "A"
