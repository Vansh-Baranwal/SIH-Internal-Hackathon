from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

import os

app = FastAPI(title="SIH Lunar Hazard Mapper - Mission API")

# Configure CORS
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "*")
origins = [frontend_origin] if frontend_origin != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MISSION_DIR = BASE_DIR / "results" / "mission_export"
ASSETS_DIR = BASE_DIR / "blender" / "assets"

def read_json_file(filename: str) -> dict:
    filepath = MISSION_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Mission export {filename} not found. Has the mission been run?")
    with open(filepath, "r") as f:
        return json.load(f)

@app.get("/api/mission/status")
def get_mission_status():
    """Returns a general overview of the available mission exports."""
    return {
        "status": "ready",
        "has_primary": (MISSION_DIR / "trajectory_primary.json").exists(),
        "has_replan": (MISSION_DIR / "replan_event.json").exists(),
        "has_replanned_trajectory": (MISSION_DIR / "trajectory_replanned.json").exists()
    }

@app.get("/api/mission/target")
def get_mission_target():
    """Returns the primary target site."""
    return read_json_file("target_site.json")

@app.get("/api/mission/trajectory/primary")
def get_primary_trajectory():
    """Returns the primary trajectory."""
    return read_json_file("trajectory_primary.json")

@app.get("/api/mission/trajectory/replanned")
def get_replanned_trajectory():
    """Returns the replanned trajectory (if any)."""
    return read_json_file("trajectory_replanned.json")

@app.get("/api/mission/replan_event")
def get_replan_event():
    """Returns the hazard replan event data."""
    return read_json_file("replan_event.json")

@app.get("/api/assets/vikram.glb")
def get_vikram_model():
    """Serves the Vikram GLB model."""
    glb_path = ASSETS_DIR / "landers" / "vikram" / "source" / "isro_chandrayyan-3_mission_lander_module_vikram.glb"
    if not glb_path.exists():
        raise HTTPException(status_code=404, detail="Vikram GLB model not found in preserved assets.")
    return FileResponse(glb_path, media_type="model/gltf-binary")

@app.get("/api/mission")
def get_full_mission():
    """Helper endpoint to fetch the entire mission state at once."""
    return {
        "target": read_json_file("target_site.json"),
        "trajectory_primary": read_json_file("trajectory_primary.json"),
        "trajectory_replanned": read_json_file("trajectory_replanned.json"),
        "replan_event": read_json_file("replan_event.json")
    }
