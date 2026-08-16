from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
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

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SR_DIR = BASE_DIR / "data" / "sr_outputs"
SR_DIR.mkdir(parents=True, exist_ok=True)

from fastapi.staticfiles import StaticFiles
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static/sr", StaticFiles(directory=SR_DIR), name="sr_outputs")

import time
from lunar_hazard_mapper.m2_super_resolution.inference import infer_geotiff

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

@app.post("/api/upload_tmc")
async def upload_tmc(file: UploadFile = File(...)):
    """Uploads a TMC image, runs CSASR M2 inference, and returns URLs for comparison."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    input_path = UPLOAD_DIR / file.filename
    output_filename = f"sr_{file.filename}"
    output_path = SR_DIR / output_filename
    
    with open(input_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    start_time = time.time()
    
    try:
        # Run M2 super-resolution!
        checkpoint_dir = BASE_DIR / "checkpoints"
        infer_geotiff(checkpoint_dir, input_path, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"M2 Inference failed: {str(e)}")
        
    end_time = time.time()
    
    # Ready for M3-M6: We could trigger a Celery task here or just return the paths
    # so the frontend can display them, and another endpoint can start M3.
    
    return JSONResponse({
        "original_url": f"/static/uploads/{file.filename}",
        "sr_url": f"/static/sr/{output_filename}",
        "inference_time_ms": round((end_time - start_time) * 1000, 2),
        "scale_factor": "32x (4x Stage1 * 4x Stage2 * 2x Bicubic)",
        "ready_for_m3": True,
        "sr_filepath": str(output_path)
    })

from lunar_hazard_mapper.api.pipeline import run_dual_pipeline

@app.post("/api/pipeline/run")
def run_full_pipeline(scene_id: str = "01_01"):
    "\""
    Executes the Dual-Path Pipeline (M1-M6) using the matching TMCORTHO and TMCDTM
    datasets. Returns the execution status and statistics for each module.
    "\""
    try:
        stats = run_dual_pipeline(scene_id)
        
        # Include fields the frontend currently expects:
        return {
            "status": "success", 
            "pipeline": stats,
            "original_url": f"/static/uploads/TMCORTHOCH_{scene_id}.tif",
            "sr_url": f"/static/sr/sr_{scene_id}.tif",
            "inference_time_ms": stats.get("m2", {}).get("runtime_s", 0) * 1000,
            "scale_factor": "32x Dual-Path",
            "ready_for_m3": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

