from typing import List, Tuple, Optional
import numpy as np
from lunar_hazard_mapper.m6_planner.schemas import ReplanEvent, SiteResult, LanderProfile, Trajectory
from lunar_hazard_mapper.m6_planner.replanning.events import ReplanContext
from lunar_hazard_mapper.m6_planner.replanning.candidate_filter import get_viable_alternatives
from lunar_hazard_mapper.m6_planner.replanning.ranking import select_best_candidate
from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
import uuid

class ReplanManager:
    """
    Coordinates the emergency re-planning cascade.
    """
    
    def __init__(self, lander: LanderProfile, candidates: List[SiteResult]):
        self.lander = lander
        self.all_candidates = candidates

    def handle_replan_event(
        self, 
        context: ReplanContext, 
        old_trajectory_id: str
    ) -> Tuple[Optional[SiteResult], Optional[Trajectory], ReplanEvent]:
        """
        Executes the re-planning cascade when an event (e.g. hazard injected) occurs.
        
        Cascade:
        EVENT -> FILTER ALTERNATIVES -> RANK -> SELECT -> GENERATE TRAJECTORY -> EMIT REPLAN EVENT
        """
        current_state_array = np.array(context.current_state)
        
        # 1. Filter viable alternatives (Reachability + Safety)
        viable_sites, rejected_sites = get_viable_alternatives(
            candidates=self.all_candidates,
            invalidated_target_id=context.current_target_id,
            lander=self.lander,
            current_state=current_state_array
        )
        
        new_trajectory_id = None
        new_trajectory = None
        
        # 2. Rank and Select
        best_site = select_best_candidate(viable_sites)
        
        # 3. Generate New Trajectory if an alternative exists
        if best_site:
            from lunar_hazard_mapper.m6_planner.adapters.terrain_provider import MockTerrainProvider
            
            new_trajectory_id = f"TRAJ_{uuid.uuid4().hex[:8].upper()}"
            new_trajectory = generate_trajectory(
                initial_state=current_state_array,
                target_pos=np.array([best_site.x, best_site.y, 0.0]),
                lander=self.lander,
                target_site_id=best_site.siteId,
                terrain_provider=MockTerrainProvider(0.0)
            )
            # Add trajectory ID to metadata
            if new_trajectory.metadata is None:
                new_trajectory.metadata = {}
            new_trajectory.metadata["trajectoryId"] = new_trajectory_id
            
        # 4. Construct Event Output
        event = ReplanEvent(
            timestamp=context.timestamp,
            trigger=context.trigger,
            oldSite=context.current_target_id,
            newSite=best_site.siteId if best_site else None,
            candidates=viable_sites,
            reason=context.reason,
            oldTrajectoryId=old_trajectory_id,
            newTrajectoryId=new_trajectory_id,
            rejectedCandidates=[{"siteId": s.siteId, "reasons": s.reasons} for s in rejected_sites],
            maneuverCost=best_site.metrics.get("maneuverCost", 0.0) if best_site else 0.0
        )
        
        return best_site, new_trajectory, event
