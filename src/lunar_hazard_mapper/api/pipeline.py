import time
import rasterio
from pathlib import Path
import numpy as np

from lunar_hazard_mapper.m2_super_resolution.inference import load_csasr_stages, infer_geotiff
from lunar_hazard_mapper.m3_terrain.dem import generate_dem
from lunar_hazard_mapper.m4_hazards.adapter import dem_to_m4_input
from lunar_hazard_mapper.m4_hazards.gradients import compute_gradients
from lunar_hazard_mapper.m4_hazards.slope import compute_slope, compute_roughness
from lunar_hazard_mapper.m4_hazards.crater import detect_craters
from lunar_hazard_mapper.m4_hazards.boulder import detect_boulders
from lunar_hazard_mapper.m4_hazards.shadow import detect_shadows
from lunar_hazard_mapper.m4_hazards.confidence import calculate_confidence
from lunar_hazard_mapper.m4_hazards.fusion import fuse_hazards
from lunar_hazard_mapper.m4_hazards.handoff import build_m4_to_m5
from lunar_hazard_mapper.m5_lander.profile import load_lander_profile
from lunar_hazard_mapper.m5_lander.evaluator import evaluate_sites
from typing import Optional, Sequence
import PIL.Image as Image

def save_hazard_artifacts(slope, continuous_risk, binary_mask, scene_id, profile, transform):
    out_dir = BASE_DIR / 'data' / 'sr_outputs'
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save PNGs for frontend preview
    # Slope (0-15 degrees visualized)
    slope_norm = np.clip(slope, 0, 15) / 15.0
    slope_img = np.zeros((slope.shape[0], slope.shape[1], 3), dtype=np.uint8)
    slope_img[:,:,0] = (slope_norm * 255).astype(np.uint8)
    slope_img[:,:,1] = (slope_norm * 128).astype(np.uint8)
    slope_img[:,:,2] = 0
    Image.fromarray(slope_img).save(out_dir / f"slope_{scene_id}.png")

    # Risk Map (0 to 1)
    risk_norm = np.clip(continuous_risk, 0, 1)
    risk_img = np.zeros((risk_norm.shape[0], risk_norm.shape[1], 3), dtype=np.uint8)
    risk_img[:,:,0] = (risk_norm * 255).astype(np.uint8)  # R
    risk_img[:,:,1] = ((1 - risk_norm) * 200).astype(np.uint8) # G
    risk_img[:,:,2] = 50 # B
    Image.fromarray(risk_img).save(out_dir / f"risk_{scene_id}.png")

    # Binary Safe/Unsafe
    bin_img = np.zeros((binary_mask.shape[0], binary_mask.shape[1], 4), dtype=np.uint8)
    bin_img[binary_mask == True] = [255, 0, 0, 180]  # Red for hazard
    bin_img[binary_mask == False] = [0, 255, 0, 80]  # Green for safe
    Image.fromarray(bin_img).save(out_dir / f"binary_{scene_id}.png")

    # 2. Save GeoTIFFs for scientific preservation
    try:
        import rasterio
        prof = profile.copy()
        prof.update(
            dtype=rasterio.float32,
            count=1,
            width=slope.shape[1],
            height=slope.shape[0],
            transform=transform
        )

        with rasterio.open(out_dir / f"slope_{scene_id}.tif", "w", **prof) as dst:
            dst.write(slope.astype(np.float32), 1)

        with rasterio.open(out_dir / f"risk_{scene_id}.tif", "w", **prof) as dst:
            dst.write(continuous_risk.astype(np.float32), 1)

        prof.update(dtype=rasterio.uint8, nodata=None)
        with rasterio.open(out_dir / f"binary_{scene_id}.tif", "w", **prof) as dst:
            dst.write(binary_mask.astype(np.uint8), 1)
    except Exception as e:
        print(f"Warning: Failed to save GeoTIFFs: {e}")

    return {
        "slope_url": f"/static/sr/slope_{scene_id}.png",
        "risk_url": f"/static/sr/risk_{scene_id}.png",
        "binary_url": f"/static/sr/binary_{scene_id}.png"
    }

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHECKPOINT_DIR = BASE_DIR / "checkpoints"

def run_dual_pipeline(scene_id: str = "01_01", subset_window=((0, 400), (0, 400)), initial_state: Optional[Sequence[float]] = None):
    """
    Executes the complete M1->M6 parallel dual-path architecture using
    the genuine TMCORTHO and TMCDTM matching pair.

    Args:
        scene_id: The scene identifier, default "01_01" for our verified pair.
        subset_window: Optional window to crop the processing so it fits in RAM and runs fast.
    """
    # Hardcoded to the verified matching pair in the dataset repository
    repo_dir = BASE_DIR.parent / "Different Repo" / "SIH" / "CODE_SIH1519_ORION SPACE SYSTEM"
    optical_path = repo_dir / "TMCORTHO5-1" / "TMCORTHO5-1" / "TMCORTHO5-1" / f"TMCORTHOCH_{scene_id}.tif"
    dem_path = repo_dir / "TMCDTM" / "TMCDTM" / f"TMCDTM_{scene_id}.tif"

    if not optical_path.exists() or not dem_path.exists():
        raise FileNotFoundError(f"Missing required datasets for {scene_id}: {optical_path} or {dem_path}")

    stats = {}

    # ---------------------------------------------------------
    # M1 & M2: SUPER RESOLUTION (OPTICAL PATH)
    # ---------------------------------------------------------
    t0 = time.time()
    with rasterio.open(optical_path) as src:
        # M1 Ingestion
        optical_array = src.read(1, window=subset_window)
        opt_profile = src.profile.copy()

    stats["m1"] = {
        "status": "success",
        "input_dimensions": f"{src.width} x {src.height}",
        "processed_dimensions": f"{optical_array.shape[1]} x {optical_array.shape[0]}"
    }

    # Write temporary crop for M2 inference
    scratch_dir = BASE_DIR / "data" / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    crop_path = scratch_dir / f"m1_crop_{scene_id}.tif"
    sr_path = BASE_DIR / 'data' / 'sr_outputs' / f'sr_{scene_id}.tif'
    sr_path.parent.mkdir(parents=True, exist_ok=True)

    opt_profile.update(width=optical_array.shape[1], height=optical_array.shape[0])
    with rasterio.open(crop_path, "w", **opt_profile) as dst:
        dst.write(optical_array, 1)

    try:
        # Load stages and infer
        infer_geotiff(CHECKPOINT_DIR, crop_path, sr_path)
        with rasterio.open(sr_path) as sr_src:
            sr_dim = f"{sr_src.width} x {sr_src.height}"
    except Exception as e:
        sr_dim = "ERROR"
        print(f"M2 Warning: {e}")

    t1 = time.time()
    stats["m2"] = {
        "status": "success" if sr_dim != "ERROR" else "error",
        "output_dimensions": sr_dim,
        "scale": "32x",
        "runtime_s": round(t1 - t0, 2),
        "output_file": str(sr_path)
    }

    # ---------------------------------------------------------
    # M3: TERRAIN PROCESSING (ELEVATION PATH)
    # ---------------------------------------------------------
    t2 = time.time()
    with rasterio.open(dem_path) as src:
        # Read matching window
        dem_array = src.read(1, window=subset_window)
        dem_res = src.res[0]
        dem_crs = str(src.crs)
        src_transform = src.window_transform(subset_window)
        dem_profile = src.profile.copy()

    # M3 explicitly requires "source_type": "measured" via the abstraction in this branch
    # Keep DEM in native geographic coordinates
    dem_obj = generate_dem(
        source={"elevation": dem_array, "source_type": "measured"},
        pixel_size_m=dem_res,
        origin_xy=(src_transform.c, src_transform.f),
        nodata=-32768.0,
        crs=dem_crs,
        assume_optical_as_elevation=False,
    )
    # Strictly enforce the actual raster transform
    dem_obj.transform = src_transform
    t3 = time.time()

    valid_elevations = dem_array[dem_array != -32768.0]
    elevation_range = f"{valid_elevations.min():.1f}m to {valid_elevations.max():.1f}m" if len(valid_elevations) > 0 else "N/A"

    stats["m3"] = {
        "status": "success",
        "dimensions": f"{dem_array.shape[1]} x {dem_array.shape[0]}",
        "resolution": dem_res,
        "elevation_range": elevation_range,
        "runtime_s": round(t3 - t2, 2)
    }

    # ---------------------------------------------------------
    # M4: HAZARD ANALYSIS
    # ---------------------------------------------------------
    t4 = time.time()
    m4_input = dem_to_m4_input(dem_obj)

    # Establish precise local metric Cartesian frame for M4/M5
    if m4_input["dx"] < 1.0: # degrees
        R_moon = 1737400.0
        m_per_deg_lat = R_moon * np.pi / 180.0

        # Calculate exact center latitude of the subset to determine longitudinal scale
        center_lat = dem_obj.transform.f + (dem_array.shape[0] / 2) * dem_obj.transform.e
        m_per_deg_lon = m_per_deg_lat * np.cos(np.radians(center_lat))

        # Assign mathematically exact metric resolution
        m4_input["dx"] = abs(dem_obj.transform.a) * m_per_deg_lon
        m4_input["dy"] = abs(dem_obj.transform.e) * m_per_deg_lat

        # M5 requires Cartesian candidates. We anchor the subset top-left at (0, 0) meters.
        m4_input["origin"]["x_m"] = 0.0
        m4_input["origin"]["y_m"] = 0.0

        # Store transformation anchor for M6 TerrainProvider
        m4_input["origin_lon_deg"] = dem_obj.transform.c
        m4_input["origin_lat_deg"] = dem_obj.transform.f
        m4_input["m_per_deg_lon"] = m_per_deg_lon
        m4_input["m_per_deg_lat"] = m_per_deg_lat

    grads = compute_gradients(m4_input)
    slope = compute_slope(grads)
    roughness = compute_roughness(m4_input, window=5)
    shadow_mask = detect_shadows(m4_input, sun_angle=15.0)
    confidence = calculate_confidence({"shadow_mask": shadow_mask})

    layers = {
        "slope_deg": slope["slope_deg"],
        "roughness": roughness,
        "confidence": confidence,
        "shadow_mask": shadow_mask,
        "dx": m4_input["dx"],
        "dy": m4_input["dy"]
    }

    craters = detect_craters(m4_input)
    boulders = detect_boulders(m4_input, min_height=0.15)
    fused = fuse_hazards(layers)

    m4_output = build_m4_to_m5(
        dem=m4_input,
        slope=slope,
        roughness=roughness,
        confidence=confidence,
        shadow_mask=shadow_mask,
        fused=fused,
        craters=craters,
        boulders=boulders
    )
    t5 = time.time()
    urls = save_hazard_artifacts(
        slope['slope_deg'],
        fused['continuous_risk'],
        fused['binary_mask'],
        scene_id,
        dem_profile,
        dem_obj.transform
    )

    stats["m4"] = {
        "status": "success",
        "hazard_layers": list(m4_output["hazards"].keys()),
        "max_slope": f"{np.nanmax(slope['slope_deg']):.2f}",
        "max_risk": f"{fused['continuous_risk'].max():.2f}",
        "runtime_s": round(t5 - t4, 2),
        **urls
    }

    # ---------------------------------------------------------
    # M5: LANDING ZONE FEASIBILITY
    # ---------------------------------------------------------
    t6 = time.time()
    vikram = load_lander_profile(BASE_DIR / "configs" / "landers" / "lander_A.yaml")
    landing_zone = evaluate_sites(None, vikram, m4_output)

    candidates = landing_zone.get("recommended_sites", [])

    t7 = time.time()
    stats["m5"] = {
        "status": "success",
        "candidates_found": len(candidates),
        "runtime_s": round(t7 - t6, 2)
    }

    # ---------------------------------------------------------
    # M6: MISSION PLANNING
    # ---------------------------------------------------------
    t8 = time.time()

    from lunar_hazard_mapper.m6_planner.adapters.m5_adapter import convert_m5_sites_to_m6_results, convert_m5_lander_to_m6_profile
    from lunar_hazard_mapper.m6_planner.trajectory.generator import generate_trajectory
    from lunar_hazard_mapper.m6_planner.schemas import ManeuverConfig
    from lunar_hazard_mapper.m6_planner.adapters.dem_provider import DemBackedTerrainProvider
    from lunar_hazard_mapper.m6_planner.reachability.evaluator import evaluate_reachability

    m6_status = "blocked"
    trajectory_info = {}

    if not candidates:
        m6_status = "no_candidates"
    elif initial_state is None:
        m6_status = "blocked"
        trajectory_info = {
            "reason": "Missing initial mission state [x, y, z, vx, vy, vz]"
        }
    else:
        try:
            m6_sites = convert_m5_sites_to_m6_results(landing_zone)
            m6_lander = convert_m5_lander_to_m6_profile(landing_zone.get("lander", {}))
            top_site = m6_sites[0]

            init_state_arr = np.array(initial_state)
            terrain_provider = DemBackedTerrainProvider(
                dem=dem_obj,
                origin_lon_deg=m4_input.get("origin_lon_deg"),
                origin_lat_deg=m4_input.get("origin_lat_deg"),
                m_per_deg_lon=m4_input.get("m_per_deg_lon"),
                m_per_deg_lat=m4_input.get("m_per_deg_lat")
            )

            is_reachable, maneuver_cost, reason = evaluate_reachability(
                site=top_site,
                lander=m6_lander,
                current_state=init_state_arr,
                config=ManeuverConfig()
            )

            if is_reachable:
                try:
                    target_z = terrain_provider.get_height(top_site.x, top_site.y)

                    trajectory = generate_trajectory(
                        initial_state=init_state_arr,
                        target_pos=np.array([top_site.x, top_site.y, target_z]),
                        lander=m6_lander,
                        target_site_id=top_site.siteId,
                        terrain_provider=terrain_provider
                    )

                    trajectory_info = {
                        "selected_site": {"x": top_site.x, "y": top_site.y, "siteId": top_site.siteId},
                        "reachable": True,
                        "delta_v": maneuver_cost,
                        "status": trajectory.status.value,
                        "points_count": len(trajectory.points) if trajectory.points else 0
                    }

                    m6_status = "success" if trajectory.status.value == "SUCCESS" else trajectory.status.value.lower()

                except ValueError as ve:
                    m6_status = "invalid"
                    trajectory_info = {
                        "selected_site": {"x": top_site.x, "y": top_site.y, "siteId": top_site.siteId},
                        "reachable": False,
                        "reason": f"Terrain Provider rejected target site coordinates: {ve}"
                    }
            else:
                m6_status = "blocked"
                trajectory_info = {
                    "selected_site": {"x": top_site.x, "y": top_site.y, "siteId": top_site.siteId},
                    "reachable": False,
                    "reason": reason
                }

        except Exception as e:
            m6_status = f"error: {str(e)}"

    t9 = time.time()
    stats["m6"] = {
        "status": m6_status,
        "trajectory": trajectory_info,
        "runtime_s": round(t9 - t8, 2)
    }

    stats["total_runtime"] = round(t9 - t0, 2)
    return stats

