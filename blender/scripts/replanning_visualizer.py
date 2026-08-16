import bpy
import json
import os
import sys

# Add current directory to path so we can import other blender scripts if run within blender
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    from trajectory_importer import create_trajectory_curve
except ImportError:
    print("M6 Error: Could not import trajectory_importer.")

def create_site_marker(name, location, color=(0.0, 1.0, 0.0, 1.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=5.0, depth=1.0, location=location)
    marker = bpy.context.active_object
    marker.name = name
    
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = 2.0
        
    marker.data.materials.append(mat)
    
    # Add text label
    bpy.ops.object.text_add(location=(location[0], location[1], location[2] + 2.0))
    txt = bpy.context.active_object
    txt.name = f"{name}_Label"
    txt.data.body = name
    txt.scale = (5.0, 5.0, 5.0)
    
    txt.data.materials.append(mat)
    return marker

def visualize_sites(selected_site_path, replan_event_path):
    site_a_loc = (0, 0, 0)
    if os.path.exists(selected_site_path):
        with open(selected_site_path, 'r') as f:
            data = json.load(f)
            site_a_loc = (data["x"], data["y"], 0)
            
    marker_a = create_site_marker("SITE_A", site_a_loc, (0.0, 1.0, 0.0, 1.0))
    
    site_b_loc = None
    if os.path.exists(replan_event_path):
        with open(replan_event_path, 'r') as f:
            evt = json.load(f)
            cands = evt.get("candidates", [])
            if cands:
                b = cands[0]
                site_b_loc = (b["x"], b["y"], 0)
                
    if site_b_loc:
        marker_b = create_site_marker("SITE_B", site_b_loc, (0.0, 0.5, 1.0, 1.0))

def visualize_diversion(filepath: str):
    """
    Loads the replanned trajectory and visualizes it as a diversion curve.
    """
    if not (filepath and os.path.exists(filepath)):
        print(f"M6 Error: Replanned trajectory file {filepath} not found.")
        return
        
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        curve_obj = create_trajectory_curve(data, curve_name="DiversionTrajectory")
        
        # Change the material color to indicate it's an emergency diversion
        if curve_obj and len(curve_obj.data.materials) > 0:
            mat = curve_obj.data.materials[0]
            if mat.use_nodes:
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Emission Color"].default_value = (1.0, 0.5, 0.0, 1.0) # Orange glow
                    
        print(f"M6: Diversion trajectory visualized.")
    except Exception as e:
        print(f"M6 Error: Failed to load diversion trajectory: {e}")

# Animation handler to change site A to invalid
EVENT_FRAME = 450
def update_hazard_visuals(scene):
    if scene.frame_current >= EVENT_FRAME:
        marker_a = bpy.data.objects.get("SITE_A")
        label_a = bpy.data.objects.get("SITE_A_Label")
        if marker_a:
            mat = marker_a.data.materials[0]
            mat.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.0, 0.0, 1.0)
            mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)
        if label_a and label_a.data.body != "SITE_A (INVALID)":
            label_a.data.body = "SITE_A (INVALID)"
    else:
        marker_a = bpy.data.objects.get("SITE_A")
        label_a = bpy.data.objects.get("SITE_A_Label")
        if marker_a:
            mat = marker_a.data.materials[0]
            mat.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.0, 1.0, 0.0, 1.0)
            mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.0, 1.0, 0.0, 1.0)
        if label_a and label_a.data.body != "SITE_A":
            label_a.data.body = "SITE_A"

def setup_hazard_animation(event_path, fps=30.0):
    global EVENT_FRAME
    if os.path.exists(event_path):
        with open(event_path, 'r') as f:
            evt = json.load(f)
            EVENT_FRAME = 1 + int(evt.get("timestamp", 15.0) * fps)
            
    bpy.app.handlers.frame_change_post.append(update_hazard_visuals)

if __name__ == "__main__":
    pass
