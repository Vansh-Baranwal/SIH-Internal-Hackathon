import bpy
import os

def load_glb(filepath, collection_name=None):
    if not os.path.exists(filepath):
        print(f"M6 Error: Asset not found: {filepath}")
        return []
        
    # Get the list of objects before import
    objs_before = set(bpy.data.objects)
    
    # Import the GLB
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    # Get the newly imported objects
    objs_after = set(bpy.data.objects)
    new_objs = list(objs_after - objs_before)
    
    if not new_objs:
        print(f"M6 Error: No objects imported from {filepath}")
        return []
        
    # Find the root objects
    roots = [obj for obj in new_objs if obj.parent is None]
    if not roots:
        roots = [new_objs[0]]
    
    return roots

def load_assets():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 1. Load Lunar Surface
    surface_path = os.path.join(base_dir, "blender", "assets", "terrain", "source", "moon_surface.glb")
    surface_roots = load_glb(surface_path)
    if surface_roots:
        surface_obj = surface_roots[0]
        surface_obj.name = "LunarTerrain"
        surface_obj.location = (1000, 0, 0)

    # 2. Load Crater
    crater_path = os.path.join(base_dir, "blender", "assets", "craters", "langrenus_crater_on_the_moon.glb")
    crater_roots = load_glb(crater_path)
    if crater_roots:
        crater_obj = crater_roots[0]
        crater_obj.name = "CraterContext"
        crater_obj.location = (-500, 500, -50)

    # 3. Load Vikram Lander
    vikram_path = os.path.join(base_dir, "blender", "assets", "landers", "vikram", "source", "isro_chandrayyan-3_mission_lander_module_vikram.glb")
    vikram_roots = load_glb(vikram_path)
    if vikram_roots:
        # PREFERRED SOLUTION: Create a dedicated Blender root controller object
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        controller = bpy.context.active_object
        controller.name = "Lander" # animation_controller.py looks for "Lander"
        
        # Parent the imported Vikram asset hierarchy under the controller
        for r in vikram_roots:
            r.parent = controller
            r.matrix_parent_inverse = controller.matrix_world.inverted()
        
    # 4. Load Rocks (Optional context)
    rock_path = os.path.join(base_dir, "blender", "assets", "environment", "Rock1.glb")
    rock_roots = load_glb(rock_path)
    if rock_roots:
        rock_obj = rock_roots[0]
        rock_obj.name = "HazardRock"
        rock_obj.location = (100, 100, 0) # Near Site A which is (100, 100)
        
    print("M6: Assets loaded successfully. Vikram Controller configured.")

if __name__ == "__main__":
    load_assets()
