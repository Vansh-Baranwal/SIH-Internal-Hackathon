import os
from pathlib import Path

BASE_DIR = Path(".")

directories = [
    "configs/landers",
    "configs/simulation",
    "src/lunar_hazard_mapper/m1_data",
    "src/lunar_hazard_mapper/m2_super_resolution",
    "src/lunar_hazard_mapper/m3_terrain",
    "src/lunar_hazard_mapper/m4_hazards",
    "src/lunar_hazard_mapper/m5_lander",
    "src/lunar_hazard_mapper/m6_planner/physics",
    "src/lunar_hazard_mapper/m6_planner/trajectory",
    "src/lunar_hazard_mapper/m6_planner/reachability",
    "src/lunar_hazard_mapper/m6_planner/replanning",
    "src/lunar_hazard_mapper/m6_planner/uncertainty",
    "data/raw",
    "data/processed",
    "synthetic/terrain",
    "synthetic/hazards",
    "synthetic/landers",
    "synthetic/scenarios",
    "models/sr",
    "outputs/dem",
    "outputs/hazards",
    "outputs/landing_sites",
    "outputs/trajectories",
    "outputs/replans",
    "blender/scripts",
    "blender/assets",
    "blender/scene",
    "scripts",
    "tests/m1",
    "tests/m2",
    "tests/m3",
    "tests/m4",
    "tests/m5",
    "tests/m6",
    "tests/integration",
    "tests/fixtures",
    "results/experiments",
    "results/metrics",
    "results/trajectories",
    "results/replans",
    "docs/members",
    "docs/architecture",
    "docs/api",
    "docs/decisions"
]

files_with_content = {
    "README.md": "# Lunar Hazard Mapper\n\nProject overview, setup, and instructions.\n",
    "CONTRIBUTING.md": "# Contributing Guidelines\n\nBranching strategy and PR rules.\n",
    "LICENSE": "MIT License\n",
    "pyproject.toml": "[project]\nname = \"lunar-hazard-mapper\"\nversion = \"0.1.0\"\ndependencies = [\n    \"numpy\",\n    \"scipy\",\n    \"pandas\",\n    \"rasterio\",\n    \"pyproj\",\n    \"shapely\",\n    \"opencv-python\",\n    \"scikit-image\",\n    \"pytest\",\n    \"jsonschema\",\n    \"matplotlib\"\n]\n",
    "requirements.txt": "numpy\nscipy\npandas\nrasterio\npyproj\nshapely\nopencv-python\nscikit-image\npytest\njsonschema\nmatplotlib\n",
    ".gitignore": "venv/\n__pycache__/\n*.pyc\ndata/raw/*\ndata/processed/*\nmodels/sr/*\noutputs/*\nresults/experiments/*\nblender/*.blend1\n!**/README.md\n!**/.gitkeep\n",
    ".gitattributes": "*.tif filter=lfs diff=lfs merge=lfs -text\n*.pt filter=lfs diff=lfs merge=lfs -text\n*.blend filter=lfs diff=lfs merge=lfs -text\n",
    
    "configs/project.yaml": "project: lunar-hazard-mapper\n",
    "configs/coordinate_convention.yaml": "coordinates:\n  x: local_east_meters\n  y: local_north_meters\n  z: local_up_meters\n",
    "configs/simulation/default.yaml": "moon:\n  gravity_mps2: 1.62\n",
    "configs/landers/lander_A.yaml": "name: Lander A\nmass_kg: 1500\nmax_slope_deg: 10\n",
    "configs/landers/lander_B.yaml": "name: Lander B\nmass_kg: 2000\nmax_slope_deg: 5\n",
    
    "src/lunar_hazard_mapper/__init__.py": "",
    "src/lunar_hazard_mapper/m1_data/__init__.py": "",
    "src/lunar_hazard_mapper/m1_data/loader.py": 'def load_tmc_tile(path):\n    """Load a TMC tile given a path."""\n    pass\n',
    "src/lunar_hazard_mapper/m1_data/metadata.py": 'def extract_metadata(path):\n    """Extract CRS, resolution, and affine transform."""\n    pass\n',
    "src/lunar_hazard_mapper/m1_data/preprocessing.py": 'def preprocess_radiometry(image):\n    """Normalize image radiometry."""\n    pass\n',
    "src/lunar_hazard_mapper/m1_data/coordinates.py": 'def convert_coords():\n    """Coordinate conversion utilities."""\n    pass\n',

    "src/lunar_hazard_mapper/m2_super_resolution/__init__.py": "",
    "src/lunar_hazard_mapper/m2_super_resolution/baselines.py": 'def bicubic_upsample(image, scale=5):\n    """Baseline nearest/bicubic interpolation."""\n    pass\n',
    "src/lunar_hazard_mapper/m2_super_resolution/models.py": 'class SRGAN:\n    """Research SR model skeleton (PyTorch)."""\n    pass\n',
    "src/lunar_hazard_mapper/m2_super_resolution/inference.py": 'def run_inference(model, image):\n    """Inference logic."""\n    pass\n',
    "src/lunar_hazard_mapper/m2_super_resolution/metrics.py": 'def calculate_psnr(pred, target):\n    """Calculate PSNR & SSIM metrics."""\n    pass\n',

    "src/lunar_hazard_mapper/m3_terrain/__init__.py": "",
    "src/lunar_hazard_mapper/m3_terrain/dem.py": 'def generate_dem(high_res_image):\n    """Generate/derive DEM from super-resolved representation."""\n    pass\n',
    "src/lunar_hazard_mapper/m3_terrain/synthetic.py": 'def create_synthetic_terrain():\n    """Create synthetic planar, ridge, and crater terrain for testing."""\n    pass\n',
    "src/lunar_hazard_mapper/m3_terrain/export.py": 'def export_dem(dem, path):\n    """Export DEM preserving CRS and pixel scale."""\n    pass\n',
    "src/lunar_hazard_mapper/m3_terrain/validation.py": 'def validate_dem(dem, reference):\n    """Validate elevation MAE/RMSE."""\n    pass\n',

    "src/lunar_hazard_mapper/m4_hazards/__init__.py": "",
    "src/lunar_hazard_mapper/m4_hazards/gradients.py": 'def compute_gradients(dem):\n    """Compute DEM gradients using Sobel or finite diff."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/slope.py": 'def compute_slope(gradients):\n    """Compute slope from gradients."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/curvature.py": 'def compute_curvature(dem):\n    """Compute second-order curvature features."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/hessian.py": 'def compute_hessian(dem):\n    """Construct Hessian [zxx, zxy; zyx, zyy]."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/eigenfeatures.py": 'def compute_eigenfeatures(hessian):\n    """Compute eigenvalues and eigenvectors."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/crater.py": 'def detect_craters(dem):\n    """Detect craters from geometry."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/boulder.py": 'def detect_boulders(dem):\n    """Detect boulders from height anomalies."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/shadow.py": 'def detect_shadows(image, sun_angle):\n    """Detect shadowed regions."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/confidence.py": 'def calculate_confidence(inputs):\n    """Estimate spatial uncertainty/confidence."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/fusion.py": 'def fuse_hazards(hazard_layers):\n    """Fuse multiple hazards into operational masks."""\n    pass\n',
    "src/lunar_hazard_mapper/m4_hazards/validation.py": 'def validate_hazards(fused_hazards):\n    """Validation metrics for detected hazards."""\n    pass\n',

    "src/lunar_hazard_mapper/m5_lander/__init__.py": "",
    "src/lunar_hazard_mapper/m5_lander/profile.py": 'class LanderProfile:\n    """Dataclass defining lander constraints."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/constraints.py": 'def check_hard_constraints(site, profile):\n    """Apply hard constraints: slope, clearance, etc."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/footprint.py": 'def evaluate_footprint(site, profile, terrain):\n    """Evaluate constraints across the 3D footprint."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/landing_zone.py": 'def analyze_landing_zone(site, radius):\n    """Analyze 24x24m area."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/site_generator.py": 'def generate_candidate_sites(terrain):\n    """Generate potential safe sites."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/scorer.py": 'def score_site(site, profile):\n    """Calculate soft scores based on risk/distance/dv."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/evaluator.py": 'def evaluate_sites(sites, profile):\n    """Run complete evaluation."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/explain.py": 'def generate_rejection_reason(site):\n    """Provide structured explanation (e.g., SLOPE_EXCEEDED)."""\n    pass\n',
    "src/lunar_hazard_mapper/m5_lander/multi_lander.py": 'def compare_landers(terrain, profiles):\n    """Compare sites across different profiles."""\n    pass\n',

    "src/lunar_hazard_mapper/m6_planner/__init__.py": "",
    "src/lunar_hazard_mapper/m6_planner/physics/__init__.py": "",
    "src/lunar_hazard_mapper/m6_planner/physics/constants.py": "G_MOON = 1.62\n",
    "src/lunar_hazard_mapper/m6_planner/physics/dynamics.py": 'def compute_forces(state):\n    """Compute translational forces F=ma."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/physics/thrust.py": 'def compute_thrust_profile():\n    """Compute thrust sequence."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/physics/integrator.py": 'def step_simulation(state, dt):\n    """Scipy solve_ivp wrapper."""\n    pass\n',

    "src/lunar_hazard_mapper/m6_planner/trajectory/__init__.py": "",
    "src/lunar_hazard_mapper/m6_planner/trajectory/generator.py": 'def generate_trajectory(start, target):\n    """Generate baseline descent trajectory."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/trajectory/constraints.py": 'def check_trajectory_constraints(traj):\n    """Ensure trajectory is physically feasible."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/trajectory/exporter.py": 'def export_trajectory(traj, format="json"):\n    """Export for Blender."""\n    pass\n',

    "src/lunar_hazard_mapper/m6_planner/reachability/__init__.py": "",
    "src/lunar_hazard_mapper/m6_planner/reachability/delta_v.py": 'def estimate_delta_v(start, target):\n    """Calculate required Delta-V."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/reachability/maneuver.py": 'def calculate_maneuver_cost():\n    """Maneuver costing."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/reachability/evaluator.py": 'def evaluate_reachability(candidates, state):\n    """Filter candidates by reachable delta-V budget."""\n    pass\n',

    "src/lunar_hazard_mapper/m6_planner/replanning/__init__.py": "",
    "src/lunar_hazard_mapper/m6_planner/replanning/events.py": 'class ReplanEvent:\n    """Structured replanning event (NEW_BOULDER, etc)."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/replanning/manager.py": 'def handle_replan_event(event):\n    """Orchestrate site invalidation and alternative selection."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/replanning/candidate_filter.py": 'def filter_candidates(candidates):\n    """Filter sites during replan."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/replanning/ranking.py": 'def rank_alternatives(candidates):\n    """Rank surviving alternatives."""\n    pass\n',

    "src/lunar_hazard_mapper/m6_planner/uncertainty/__init__.py": "",
    "src/lunar_hazard_mapper/m6_planner/uncertainty/noise.py": 'def apply_noise(state):\n    """Add sensor/state noise."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/uncertainty/monte_carlo.py": 'def run_mc_simulations():\n    """Repeated simulations with variation."""\n    pass\n',
    "src/lunar_hazard_mapper/m6_planner/uncertainty/analysis.py": 'def analyze_uncertainty():\n    """Evaluate landing success probabilities."""\n    pass\n',
    
    "scripts/generate_synthetic_data.py": "print('Generating synthetic data...')\n",
    "scripts/run_pipeline.py": "print('Running pipeline...')\n",
    "scripts/run_smoke_test.py": "print('Running smoke test...')\n",
    "scripts/validate_contracts.py": "print('Validating data contracts...')\n",

    "docs/SETUP.md": "# Setup Instructions\n\n1. Clone repo\n2. Create virtual environment\n3. Install dependencies (`pip install -r requirements.txt`)\n4. Run tests (`pytest tests/`)\n5. Generate synthetic data (`python scripts/generate_synthetic_data.py`)\n6. Run pipeline (`python scripts/run_pipeline.py`)\n7. Open Blender\n8. Run Blender scripts\n",
    "docs/EXPERIMENT_TEMPLATE.md": "# Experiment Log\n\nDate:\nMember:\nModel Version:\nDataset Version:\nConfiguration:\nParameters:\nMetrics:\nOutput Location:\nCheckpoint ID:\nNotes:\n",
    
    "docs/members/m1_data_geospatial.md": "# M1 - Data Acquisition & Preprocessing\n\nResponsibilities: TMC imagery/data ingestion, CRS, tiling, reference data.\n",
    "docs/members/m2_super_resolution.md": "# M2 - Super Resolution\n\nResponsibilities: SRGAN research, interpolation baseline, metric calculation.\n",
    "docs/members/m3_dem_terrain.md": "# M3 - DEM & Terrain\n\nResponsibilities: Elevation derivation, DEM validation, units definition.\n",
    "docs/members/m4_hazards.md": "# M4 - Hazard Detection\n\nResponsibilities: Slope, curvature, Hessian, boulders, craters, confidence.\n",
    "docs/members/m5_lander_site.md": "# M5 - Lander Intelligence\n\nResponsibilities: Profile constraints, footprint evaluation, explainable rejections.\n",
    "docs/members/m6_physics_blender.md": "# M6 - Physics & Simulation\n\nResponsibilities: 3-DOF descent, replanning engine, Blender UI and visualization.\n",

    "docs/architecture/SYSTEM_ARCHITECTURE.md": "# System Architecture\n\nComplete project design, modules, dependencies.\n\n*Important:* Do not implement complex production algorithms merely to fill files. Create clean, executable starter implementations for every module, but clearly mark research/placeholder algorithms and avoid fake accuracy. Prioritize correct interfaces, tests, synthetic fixtures, and modularity.\n",
    "docs/architecture/DATA_FLOW.md": "# Data Flow\n\nM1 -> M2 -> M3 -> M4 -> M5 -> M6 -> Blender\n",
    "docs/architecture/BUILD_ORDER.md": "# Build Order\n\nPhase 1: Skeleton + synthetic data\nPhase 2: First integration\nPhase 3: Core algorithms\nPhase 4: Differentiation\nPhase 5: Validation\nPhase 6: Final pipeline optimization\n",
    "docs/architecture/DEFINITION_OF_DONE.md": "# Definition of Done\n\nExecutable, documented, tested, synthetic data passes, example artifact generated.\n",

    "docs/api/DATA_CONTRACTS.md": "# Data Contracts\n\nInterfaces between M1 through M6.\n",
    "docs/api/EXAMPLE_SCHEMAS.md": "# Example Schemas\n\nJSON examples for payloads.\n",
    "docs/api/INTEGRATION_GUIDE.md": "# Integration Guide\n\nFile formats, coordinate conversions, and metadata rules.\n",

    "docs/decisions/0001-coordinate-convention.md": "# Coordinate Convention\n\nFixed coordinate standard for simulation region.\n",
    "docs/decisions/0002-python-source-of-truth.md": "# Python as Source of Truth\n\nBlender visualizes; Python calculates.\n",
    
    "blender/scripts/scene_init.py": "import bpy\n\ndef init_scene():\n    pass\n",
    "blender/scripts/terrain_import.py": "import bpy\n\ndef import_terrain():\n    pass\n",
    "blender/scripts/trajectory_import.py": "import bpy\n\ndef import_trajectory():\n    pass\n",
    "blender/scripts/telemetry.py": "import bpy\n\ndef setup_telemetry():\n    pass\n",
    "blender/scripts/click_to_land.py": "import bpy\n\ndef setup_click_to_land():\n    pass\n",
    "blender/scripts/hazard_injection.py": "import bpy\n\ndef inject_hazard_ui():\n    pass\n",
    
    "synthetic/terrain/flat.py": "def generate_flat_terrain():\n    pass\n",
    "synthetic/terrain/slope.py": "def generate_slope():\n    pass\n",
    "synthetic/terrain/crater.py": "def generate_crater():\n    pass\n",
    "synthetic/terrain/boulder.py": "def generate_boulder():\n    pass\n",
    "synthetic/terrain/combined.py": "def generate_combined():\n    pass\n",

    "tests/integration/test_end_to_end.py": "def test_end_to_end():\n    assert True\n"
}

# Directories that just need a .gitkeep or README to be tracked
empty_dirs = [
    "data/raw", "data/processed", "models/sr", "outputs/dem", "outputs/hazards", 
    "outputs/landing_sites", "outputs/trajectories", "outputs/replans", 
    "results/experiments", "results/metrics", "results/trajectories", "results/replans"
]

def main():
    for d in directories:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
        
    for filepath, content in files_with_content.items():
        p = BASE_DIR / filepath
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
            
    for ed in empty_dirs:
        p = BASE_DIR / ed / "README.md"
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"# {ed}\\n\\nGenerated files are stored here. Do not commit large artifacts.\\n")

if __name__ == "__main__":
    main()
