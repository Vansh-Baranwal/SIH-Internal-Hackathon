import bpy
import json
import os
import math

def animate_lander_along_trajectory(lander_obj, trajectory_data, fps=30.0, start_frame=1):
    """
    Animates the lander object using explicit keyframes from trajectory points.
    
    Args:
        lander_obj: Blender object representing the lander.
        trajectory_data: The parsed trajectory JSON dictionary.
        fps: Frames per second to map simulation time to frames.
        start_frame: The frame at which animation begins.
    """
    points = trajectory_data.get("points", [])
    if not points:
        print("M6 Error: No points to animate.")
        return
        
    # Ensure animation data exists
    if not lander_obj.animation_data:
        lander_obj.animation_data_create()
        
    action = bpy.data.actions.new(name=f"Anim_{lander_obj.name}")
    lander_obj.animation_data.action = action
    
    # Calculate end frame
    max_t = points[-1]["t"]
    end_frame = start_frame + int(max_t * fps)
    
    # Set scene end frame if it's longer
    if bpy.context.scene.frame_end < end_frame:
        bpy.context.scene.frame_end = end_frame
        
    for pt in points:
        t = pt["t"]
        frame = start_frame + int(t * fps)
        
        # Set location
        lander_obj.location = (pt["x"], pt["y"], pt["z"])
        lander_obj.keyframe_insert(data_path="location", frame=frame)
        
        # Simple attitude calculation (point nozzle opposite to velocity vector)
        vx, vy, vz = pt["vx"], pt["vy"], pt["vz"]
        speed = math.sqrt(vx**2 + vy**2 + vz**2)
        
        if speed > 0.1:
            # Calculate pitch/roll to lean into the velocity vector for deceleration
            # Note: A real lander leans opposite to velocity to thrust and slow down.
            # Z axis of lander is up. We want thrust vector (Z) to point against velocity.
            # Very simplified mock rotation:
            pitch = math.atan2(vy, -vz)
            roll = math.atan2(vx, -vz)
            
            lander_obj.rotation_euler = (pitch, roll, 0)
        else:
            lander_obj.rotation_euler = (0, 0, 0) # Upright
            
        lander_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        
    print(f"M6: Animated '{lander_obj.name}' from frame {start_frame} to {end_frame}.")
    return end_frame

def load_dual_trajectories(primary_path, replanned_path, event_path, lander_name="Lander", fps=30.0):
    lander = bpy.data.objects.get(lander_name)
    if not lander:
        print(f"M6 Error: Lander '{lander_name}' not found.")
        return
        
    event_time = 15.0 # fallback
    if os.path.exists(event_path):
        try:
            with open(event_path, 'r') as f:
                evt = json.load(f)
                event_time = evt.get("timestamp", 15.0)
        except Exception as e:
            print(f"M6 Error reading event file: {e}")
            
    # Load primary points
    primary_points = []
    if os.path.exists(primary_path):
        try:
            with open(primary_path, 'r') as f:
                primary_data = json.load(f)
                primary_points = primary_data.get("points", [])
        except Exception as e:
            print(f"M6 Error reading primary trajectory: {e}")
            
    # Load replanned points
    replanned_points = []
    if os.path.exists(replanned_path):
        try:
            with open(replanned_path, 'r') as f:
                replanned_data = json.load(f)
                replanned_points = replanned_data.get("points", [])
        except Exception as e:
            print(f"M6 Error reading replanned trajectory: {e}")

    # Combine points: primary up to event_time, then replanned
    combined_points = []
    for pt in primary_points:
        if pt["t"] <= event_time:
            combined_points.append(pt)
            
    # Replanned trajectory starts at t=0 relative to the original timeline?
    # No, looking at the JSON, replanned_trajectory points start at t=0 which is the event time.
    # WAIT! Let's check replanned_trajectory.json. The first point has t=0.0 but coordinates match the event state (x=265, z=977).
    # Ah, let's look at the replanned_trajectory.json first point.
    
    # Actually, in replanned_trajectory.json, t starts at 0.0, but the event time was 15.0. 
    # We should offset the replanned t by event_time to place it correctly on the timeline.
    for pt in replanned_points:
        adjusted_pt = pt.copy()
        adjusted_pt["t"] = pt["t"] + event_time
        combined_points.append(adjusted_pt)
        
    # Animate combined
    if combined_points:
        animate_lander_along_trajectory(lander, {"points": combined_points}, fps=fps)

if __name__ == "__main__":
    pass
