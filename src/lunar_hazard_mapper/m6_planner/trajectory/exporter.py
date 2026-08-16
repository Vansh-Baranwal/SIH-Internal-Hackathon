import json
from lunar_hazard_mapper.m6_planner.schemas import Trajectory

class TrajectoryExporter:
    """
    Handles serialization of generated trajectories to JSON for Blender ingestion.
    """
    
    @staticmethod
    def export_to_json(trajectory: Trajectory, filepath: str) -> None:
        """
        Exports the Trajectory Pydantic model to a JSON file.
        
        Args:
            trajectory: The generated trajectory.
            filepath: Destination file path.
        """
        with open(filepath, 'w') as f:
            # model_dump_json is available in Pydantic v2
            # For pydantic v1 it would be json()
            if hasattr(trajectory, 'model_dump_json'):
                json_str = trajectory.model_dump_json(indent=2)
            else:
                json_str = trajectory.json(indent=2)
            f.write(json_str)
