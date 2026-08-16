import random
from typing import List
from lunar_hazard_mapper.m6_planner.schemas import LanderProfile, SiteResult

class MockM5Provider:
    """
    Deterministic mock provider for M5 LanderProfile and SiteResult data.
    Ensures M6 can be developed independently of M5.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def get_lander_profile(self, name: str = "Research Lander A") -> LanderProfile:
        return LanderProfile(
            name=name,
            mass=1500.0,
            maxSlope=12.0,
            maxVz=-3.0,
            maxVxy=1.5,
            footprint=3.5,
            clearance=0.8,
            deltaVBudget=50.0,
            uncertaintyLimit=0.9
        )

    def generate_candidate_sites(self, count: int = 10, center_x: float = 0.0, center_y: float = 0.0, spread: float = 500.0) -> List[SiteResult]:
        """
        Generates a deterministic set of candidate landing sites with mock feasibility scores.
        """
        sites = []
        for i in range(count):
            x = center_x + self.rng.uniform(-spread, spread)
            y = center_y + self.rng.uniform(-spread, spread)
            
            # 80% chance a site is considered feasible by M5
            feasible = self.rng.random() > 0.2
            score = self.rng.uniform(0.7, 0.99) if feasible else self.rng.uniform(0.1, 0.5)
            
            reasons = [] if feasible else ["Mock: Slope exceeds 12 deg", "Mock: Crater risk high"]
            
            site = SiteResult(
                siteId=f"SITE_{i:03d}",
                x=x,
                y=y,
                score=score,
                feasible=feasible,
                reasons=reasons,
                metrics={
                    "slope": self.rng.uniform(1.0, 15.0),
                    "craterRisk": self.rng.uniform(0.0, 1.0),
                    "boulderRisk": self.rng.uniform(0.0, 1.0),
                    "confidence": self.rng.uniform(0.6, 1.0),
                    "distance": (x**2 + y**2)**0.5
                }
            )
            sites.append(site)
        return sites
