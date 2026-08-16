import bpy
from bpy_extras import view3d_utils

class M6ClickToLandOperator(bpy.types.Operator):
    """Click on terrain to select a manual landing site"""
    bl_idname = "view3d.m6_click_to_land"
    bl_label = "M6 Click to Land"
    
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Raycast from mouse position to terrain
            region = context.region
            rv3d = context.region_data
            coord = event.mouse_region_x, event.mouse_region_y
            
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
            
            # Use raycast to find hit point on LunarTerrain
            depsgraph = context.evaluated_depsgraph_get()
            hit, loc, norm, index, obj, matrix = context.scene.ray_cast(depsgraph, ray_origin, view_vector)
            
            if hit and obj.name == "LunarTerrain":
                print(f"\n======================================")
                print(f"M6: Click-to-Land selected coordinates:")
                print(f"X: {loc.x:.2f} m, Y: {loc.y:.2f} m, Z: {loc.z:.2f} m")
                print(f"Triggering M5/M6 Site Evaluator Pipeline...")
                print(f"======================================\n")
                
                # In a full integration, this would write to a temporary JSON and trigger
                # the external Python M6 process, then wait for the trajectory.json response.
                self.report({'INFO'}, f"Target set: {loc.x:.1f}, {loc.y:.1f}")
            
            return {'FINISHED'}
            
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            self.report({'INFO'}, "Click on the Lunar Terrain to set landing site.")
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(M6ClickToLandOperator)

def unregister():
    bpy.utils.unregister_class(M6ClickToLandOperator)

if __name__ == "__main__":
    register()
    # Test execution
    # bpy.ops.view3d.m6_click_to_land('INVOKE_DEFAULT')
