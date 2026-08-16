import bpy
import json
import os

def create_trajectory_curve(trajectory_data, curve_name="TrajectoryCurve"):
    """
    Creates a Bezier Curve in Blender from a list of trajectory points.
    
    Args:
        trajectory_data: Dictionary representing the Trajectory schema.
        curve_name: Name for the generated Blender curve object.
    """
    points = trajectory_data.get("points", [])
    if not points:
        print(f"M6 Error: No points found in trajectory data for {curve_name}.")
        return None
        
    # Create curve data
    curve_data = bpy.data.curves.new(name=f"{curve_name}_Data", type='CURVE')
    curve_data.dimensions = '3D'
    
    # We want a visible path (tube)
    curve_data.bevel_depth = 0.5
    curve_data.bevel_resolution = 4
    
    # Add a polyline spline
    spline = curve_data.splines.new(type='POLY')
    spline.points.add(len(points) - 1) # One point already exists
    
    for i, pt in enumerate(points):
        # Spline point coordinates are (x, y, z, w) where w is weight
        spline.points[i].co = (pt["x"], pt["y"], pt["z"], 1.0)
        
    # Create object and link to scene
    curve_obj = bpy.data.objects.new(curve_name, curve_data)
    bpy.context.collection.objects.link(curve_obj)
    
    # Assign a glowing material
    mat = bpy.data.materials.new(name=f"{curve_name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Emission Color"].default_value = (0.0, 0.8, 1.0, 1.0) # Cyan glow
        bsdf.inputs["Emission Strength"].default_value = 5.0
        
    if len(curve_obj.data.materials) == 0:
        curve_obj.data.materials.append(mat)
        
    print(f"M6: Trajectory curve '{curve_name}' generated with {len(points)} points.")
    return curve_obj

def load_and_visualize_trajectory(filepath: str, curve_name="PrimaryTrajectory"):
    """
    Loads JSON trajectory and creates the visual curve.
    """
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            create_trajectory_curve(data, curve_name)
        except Exception as e:
            print(f"M6 Error: Could not load trajectory file: {e}")
    else:
        print(f"M6 Error: Trajectory file {filepath} not found.")

if __name__ == "__main__":
    # Example usage:
    # load_and_visualize_trajectory("results/m6_demo/trajectory.json", "PrimaryTrajectory")
    pass
