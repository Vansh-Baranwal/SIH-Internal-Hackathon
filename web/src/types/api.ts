export interface TrajectoryPoint {
  t: number;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  attitude: any;
}

export interface Trajectory {
  targetSiteId: string;
  status: string;
  points: TrajectoryPoint[];
  initialState: TrajectoryPoint;
  finalState: TrajectoryPoint;
  metadata: {
    controller: string;
    duration_s: number;
    status_code: number;
    trajectoryId?: string;
  };
}

export interface TargetSite {
  siteId: string;
  x: number;
  y: number;
  score: number;
  feasible: boolean;
  reasons: string[];
  metrics: any;
}

export interface ReplanEvent {
  timestamp: number;
  trigger: string;
  oldSite: string;
  newSite: string;
  candidates: TargetSite[];
  reason: string;
  oldTrajectoryId: string;
  newTrajectoryId: string;
  rejectedCandidates: any[];
  maneuverCost: number;
}

export interface MissionData {
  target: TargetSite;
  trajectory_primary: Trajectory;
  trajectory_replanned: Trajectory | null;
  replan_event: ReplanEvent | null;
}
