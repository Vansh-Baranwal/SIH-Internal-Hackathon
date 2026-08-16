import bpy
import bmesh
import json
import os

def create_terrain_mesh(name="LunarTerrain", width=200, height=200, resolution=5.0, height_data=None):
    """
    Creates a terrain mesh from height data.
    If height_data is None, generates a flat plane.
    
    Args:
        name: Name of the mesh object.
        width: Number of vertices in X direction.
        height: Number of vertices in Y direction.
        resolution: Meters per vertex (scale).
        height_data: 1D list of Z values, length must be width * height.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    verts = []
    # Create vertices
    # Center the terrain at (0,0)
    offset_x = (width * resolution) / 2.0
    offset_y = (height * resolution) / 2.0
    
    for y in range(height):
        for x in range(width):
            loc_x = (x * resolution) - offset_x
            loc_y = (y * resolution) - offset_y
            
            idx = y * width + x
            loc_z = height_data[idx] if height_data else 0.0
            
            v = bm.verts.new((loc_x, loc_y, loc_z))
            verts.append(v)
            
    bm.verts.ensure_lookup_table()
    
    # Create faces
    for y in range(height - 1):
        for x in range(width - 1):
            v1 = verts[y * width + x]
            v2 = verts[y * width + (x + 1)]
            v3 = verts[(y + 1) * width + (x + 1)]
            v4 = verts[(y + 1) * width + x]
            
            try:
                bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                pass # Face already exists or invalid
                
    bm.to_mesh(mesh)
    bm.free()
    
    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True
        
    # Basic lunar material
    mat = bpy.data.materials.new(name="LunarMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
    
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
        
    print(f"M6: Terrain '{name}' generated successfully.")

def import_dem(filepath: str = None):
    """
    Imports DEM data to build the terrain.
    """
    height_data = None
    width, height_y = 200, 200
    resolution = 5.0
    
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                width = data.get("width", 200)
                height_y = data.get("height", 200)
                resolution = data.get("resolution", 5.0)
                height_data = data.get("heights", None)
            print(f"M6: Successfully loaded DEM from {filepath}")
        except Exception as e:
            print(f"M6 Error: Could not load DEM file: {e}")
    else:
        print("M6: No DEM file provided or found. Using default flat mock terrain.")
        
    create_terrain_mesh("LunarTerrain", width=width, height=height_y, resolution=resolution, height_data=height_data)

if __name__ == "__main__":
    # In practice, this script is called with arguments or environment variables
    # determining the location of the exported M3 DEM mock.
    # For independent testing, we default to a flat mock.
    import_dem()
