import bpy
import math

def clean_scene():
    """
    Removes all default objects (Cube, Light, Camera, etc.) from the scene 
    to prepare a clean slate for the Lunar Hazard Mapper.
    """
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Also clean orphaned data blocks to prevent memory leaks during reloads
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

def setup_lighting():
    """
    Sets up a directional light simulating the Sun for lunar terrain visualization.
    """
    # Create sun light
    light_data = bpy.data.lights.new(name="LunarSun", type='SUN')
    light_data.energy = 5.0 # High intensity for stark contrast
    light_data.angle = math.radians(0.53) # Roughly solar angular diameter
    
    # Create light object and link to scene
    light_obj = bpy.data.objects.new(name="LunarSun", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    
    # Position and orient the sun (low grazing angle emphasizes terrain features)
    light_obj.location = (0, 0, 1000)
    light_obj.rotation_euler = (math.radians(60), math.radians(0), math.radians(45))

def setup_camera():
    """
    Sets up the primary mission control camera.
    """
    cam_data = bpy.data.cameras.new("MissionCamera")
    cam_data.lens = 35 # 35mm focal length
    cam_data.clip_end = 50000 # High clipping plane for large lunar terrains
    
    cam_obj = bpy.data.objects.new("MissionCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    
    # Set it as the active scene camera
    bpy.context.scene.camera = cam_obj
    
    # Position it at an isometric-style overview angle
    cam_obj.location = (-1000, -1000, 1000)
    cam_obj.rotation_euler = (math.radians(60), 0, math.radians(-45))

def setup_scene():
    """
    Main entry point for scene initialization.
    Designed for Blender 4.x APIs.
    """
    # 1. Clean the default scene
    clean_scene()
    
    # 2. Setup environment
    setup_lighting()
    setup_camera()
    
    # 3. Configure render settings for high-contrast lunar environment
    bpy.context.scene.render.engine = 'CYCLES' # Use Cycles for realistic shadows
    if hasattr(bpy.context.scene.cycles, 'device'):
        bpy.context.scene.cycles.device = 'GPU'
        
    # Black background for space
    if not bpy.context.scene.world:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    bpy.context.scene.world.use_nodes = True
    bg_node = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0) # Absolute black
        
    print("M6: Blender scene initialized successfully.")

if __name__ == "__main__":
    setup_scene()
