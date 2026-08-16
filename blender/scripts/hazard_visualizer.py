import bpy
import json
import os

def apply_hazard_vertex_colors(mesh_obj, hazard_data):
    """
    Applies hazard scores to the mesh as Vertex Colors (Color Attributes in Blender 4.x).
    
    Args:
        mesh_obj: The terrain blender object.
        hazard_data: A list of scalar values [0.0 to 1.0] representing hazard severity,
                     ordered matching the mesh vertices.
    """
    mesh = mesh_obj.data
    
    # In Blender 3.2+, vertex colors were renamed to Color Attributes
    # Create a new color attribute on the vertex domain
    if not mesh.color_attributes:
        color_attr = mesh.color_attributes.new(name="HazardHeatmap", type='BYTE_COLOR', domain='POINT')
    else:
        color_attr = mesh.color_attributes.get("HazardHeatmap")
        if not color_attr:
            color_attr = mesh.color_attributes.new(name="HazardHeatmap", type='BYTE_COLOR', domain='POINT')
            
    # Iterate through vertices and assign colors based on hazard score
    # For safety/hazard: Green=Safe(0.0), Red=Hazard(1.0)
    for i, v in enumerate(mesh.vertices):
        score = hazard_data[i] if hazard_data and i < len(hazard_data) else 0.0
        
        # Color gradient: 0.0 -> (0, 1, 0, 1), 1.0 -> (1, 0, 0, 1)
        r = score
        g = 1.0 - score
        b = 0.0
        a = 1.0
        
        color_attr.data[i].color = (r, g, b, a)

    # Setup the material to use the Color Attribute
    mat = mesh_obj.data.materials.get("LunarMaterial")
    if mat and mat.use_nodes:
        tree = mat.node_tree
        
        # Check if Color Attribute node exists
        attr_node = tree.nodes.get("HazardColor")
        if not attr_node:
            attr_node = tree.nodes.new(type="ShaderNodeAttribute")
            attr_node.name = "HazardColor"
            attr_node.attribute_name = "HazardHeatmap"
            attr_node.location = (-400, 200)
            
        # Mix it with the base color
        mix_node = tree.nodes.get("HazardMix")
        if not mix_node:
            mix_node = tree.nodes.new(type="ShaderNodeMix")
            mix_node.name = "HazardMix"
            mix_node.data_type = 'RGBA'
            mix_node.blend_type = 'MULTIPLY'
            mix_node.inputs[0].default_value = 0.5 # Mix factor
            mix_node.location = (-200, 200)
            
        bsdf = tree.nodes.get("Principled BSDF")
        
        if attr_node and mix_node and bsdf:
            # Set base color input of mix node to default gray
            mix_node.inputs[6].default_value = (0.5, 0.5, 0.5, 1.0) # Base lunar gray (Input A)
            
            # Connect Attribute Color -> Mix Input B
            tree.links.new(attr_node.outputs["Color"], mix_node.inputs[7])
            
            # Connect Mix Output -> BSDF Base Color
            tree.links.new(mix_node.outputs[2], bsdf.inputs["Base Color"])
            
    print("M6: Hazard heatmap applied to terrain.")

def load_and_visualize_hazards(filepath: str = None):
    """
    Loads mock M4 hazard data and applies it to the LunarTerrain.
    """
    terrain = bpy.data.objects.get("LunarTerrain")
    if not terrain:
        print("M6 Error: LunarTerrain not found. Cannot apply hazards.")
        return
        
    hazard_data = None
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                hazard_data = data.get("hazard_scores", None)
            print(f"M6: Successfully loaded Hazard data from {filepath}")
        except Exception as e:
            print(f"M6 Error: Could not load Hazard file: {e}")
    else:
        print("M6: No Hazard file provided. Using mock hazard pattern.")
        # Create a mock pattern based on distance from center
        hazard_data = []
        import math
        for v in terrain.data.vertices:
            dist = math.sqrt(v.co.x**2 + v.co.y**2)
            # Make the center safe, edges hazardous
            score = min(1.0, max(0.0, (dist - 100) / 400.0))
            hazard_data.append(score)
            
    apply_hazard_vertex_colors(terrain, hazard_data)

if __name__ == "__main__":
    load_and_visualize_hazards()
