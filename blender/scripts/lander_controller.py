import bpy

def create_lander_model(name="Lander"):
    """
    Creates a simple placeholder low-poly lander model for visualization.
    """
    # Check if lander already exists
    if bpy.data.objects.get(name):
        return bpy.data.objects[name]
        
    # 1. Main body (Cylinder)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=2.0, location=(0, 0, 1.0))
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    
    # 2. Engine nozzle (Cone)
    bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0.0, depth=1.0, location=(0, 0, -0.5))
    nozzle = bpy.context.active_object
    nozzle.name = f"{name}_Nozzle"
    # Parent nozzle to body
    nozzle.parent = body
    
    # 3. Create a master Empty to act as the root coordinate frame
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    lander_root = bpy.context.active_object
    lander_root.name = name
    
    # Parent body to root
    body.parent = lander_root
    
    # Add gold foil material to body
    mat = bpy.data.materials.new(name="KaptonFoil")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.1, 1.0) # Gold
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.2
    
    if len(body.data.materials) == 0:
        body.data.materials.append(mat)
        
    print(f"M6: Created placeholder lander asset '{name}'.")
    return lander_root

if __name__ == "__main__":
    create_lander_model()
