import sys
import os
import bpy

# add blender/scripts to sys path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

import scene_init
import asset_loader
import trajectory_importer
import replanning_visualizer
import animation_controller
import mission_ui

def main():
    base_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    results_dir = os.path.join(base_dir, "results", "m6_demo")
    
    selected_site_path = os.path.join(results_dir, "selected_site.json")
    trajectory_path = os.path.join(results_dir, "trajectory.json")
    replan_event_path = os.path.join(results_dir, "replan_event.json")
    replanned_trajectory_path = os.path.join(results_dir, "replanned_trajectory.json")
    
    # 1. Init Scene
    scene_init.setup_scene()
    
    # 2. Load Assets
    asset_loader.load_assets()
    
    # 3. Visualize Trajectories
    trajectory_importer.load_and_visualize_trajectory(trajectory_path, "PrimaryTrajectory")
    replanning_visualizer.visualize_diversion(replanned_trajectory_path)
    
    # 4. Visualize Sites and Events
    replanning_visualizer.visualize_sites(selected_site_path, replan_event_path)
    replanning_visualizer.setup_hazard_animation(replan_event_path, fps=30.0)
    
    # 5. Animate Lander
    animation_controller.load_dual_trajectories(trajectory_path, replanned_trajectory_path, replan_event_path, lander_name="Lander", fps=30.0)
    
    # 6. Mission HUD
    mission_ui.setup_telemetry_ui()
    mission_ui.init_hud_state(replan_event_path)
    mission_ui.register_telemetry_handler()
    
    # Save the scene
    output_blend = os.path.join(base_dir, "results", "m6_demo", "m6_visualization.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    
    print("==================================================")
    print(" M6 BLENDER VISUALIZATION READY")
    print(f" Saved to: {output_blend}")
    print("==================================================")

if __name__ == "__main__":
    main()
