import bpy
import json
import os

def visualize_hazard_event(filepath: str):
    """
    Reads the replan_event.json and creates a visual hazard marker at the invalidated site.
    """
    if not (filepath and os.path.exists(filepath)):
        print(f"M6 Error: Replan event file {filepath} not found.")
        return
        
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"M6 Error: Failed to load event data: {e}")
        return
        
    # We need to know the coordinates of the old site.
    # In a full integration, the event would include the coordinates or we'd look them up.
    # For now, we will place a hazard marker at the end of the primary trajectory.
    primary_curve = bpy.data.objects.get("PrimaryTrajectory")
    if not primary_curve:
        print("M6 Warning: PrimaryTrajectory not found, cannot place hazard marker.")
        return
        
    # Get last point of primary trajectory
    spline = primary_curve.data.splines[0]
    end_pt = spline.points[-1].co
    
    # Create Hazard Marker (Red X or Sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=10.0, location=(end_pt.x, end_pt.y, end_pt.z))
    marker = bpy.context.active_object
    marker.name = "Hazard_Marker"
    
    mat = bpy.data.materials.new(name="Hazard_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.0, 0.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 5.0
        
    if len(marker.data.materials) == 0:
        marker.data.materials.append(mat)
        
    # Trigger HUD warning
    status_text = bpy.data.objects.get("Telemetry_Status")
    if status_text:
        status_text.data.body = f"CRITICAL: {data.get('trigger', 'HAZARD')}"
        status_text.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.0, 0.0, 1.0)

    print(f"M6: Hazard event visualized at old site '{data.get('oldSite')}'.")

if __name__ == "__main__":
    # visualize_hazard_event("results/m6_demo/replan_event.json")
    pass
