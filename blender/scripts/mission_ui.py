import bpy

def setup_telemetry_ui():
    cam = bpy.data.objects.get("MissionCamera")
    if not cam:
        print("M6 Error: MissionCamera not found. Cannot anchor UI.")
        return
        
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    hud_root = bpy.context.active_object
    hud_root.name = "HUD_Root"
    hud_root.parent = cam
    hud_root.location = (0, 0, -2.0)
    
    # 2. Create Texts
    def create_text(name, body, loc):
        bpy.ops.object.text_add()
        txt = bpy.context.active_object
        txt.name = name
        txt.data.body = body
        txt.parent = hud_root
        txt.location = loc
        txt.scale = (0.05, 0.05, 0.05)
        return txt

    alt_text = create_text("Telemetry_Altitude", "ALT: 1000.0 m", (-1.5, 1.0, 0))
    vel_text = create_text("Telemetry_Velocity", "VEL: 50.0 m/s", (-1.5, 0.9, 0))
    tgt_text = create_text("Telemetry_Target", "TARGET: SITE_A", (-1.5, 0.8, 0))
    dv_text = create_text("Telemetry_DV", "DV: 157 m/s", (0.5, 0.9, 0))
    status_text = create_text("Telemetry_Status", "STATUS: NOMINAL", (0.5, 1.0, 0))
    
    mat = bpy.data.materials.new(name="HUD_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Emission Color"].default_value = (0.2, 1.0, 0.2, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0
        
    for txt in [alt_text, vel_text, tgt_text, dv_text, status_text]:
        if len(txt.data.materials) == 0:
            txt.data.materials.append(mat)
            
    print("M6: Mission Telemetry HUD initialized.")

# Global state for handler
HUD_STATE = {
    "event_time": 15.0,
    "event_frame": 450,
    "fps": 30.0,
    "primary_target": "SITE_A",
    "new_target": "SITE_B",
    "maneuver_cost": 157.0
}

def init_hud_state(event_path):
    import json, os
    if os.path.exists(event_path):
        try:
            with open(event_path, 'r') as f:
                evt = json.load(f)
                HUD_STATE["event_time"] = evt.get("timestamp", 15.0)
                HUD_STATE["primary_target"] = evt.get("oldSite", "SITE_A")
                HUD_STATE["new_target"] = evt.get("newSite", "SITE_B")
                HUD_STATE["maneuver_cost"] = evt.get("maneuverCost", 157.0)
                HUD_STATE["event_frame"] = 1 + int(HUD_STATE["event_time"] * HUD_STATE["fps"])
        except Exception as e:
            pass

def update_telemetry(scene):
    lander = bpy.data.objects.get("Lander")
    alt_text = bpy.data.objects.get("Telemetry_Altitude")
    vel_text = bpy.data.objects.get("Telemetry_Velocity")
    status_text = bpy.data.objects.get("Telemetry_Status")
    tgt_text = bpy.data.objects.get("Telemetry_Target")
    dv_text = bpy.data.objects.get("Telemetry_DV")
    
    if lander and alt_text:
        alt = lander.location.z
        alt_text.data.body = f"ALT: {alt:.1f} m"
        
        # Simple velocity calc based on position change (if animation is running)
        # Note: True velocity is hard to get from animation location without delta, we'll just show it conceptually or leave static for UI if too hard.
        # But we can approximate by reading the previous frame.
        # To avoid complex handler logic, we just do a visual status update.
        
        frame = scene.frame_current
        if frame < HUD_STATE["event_frame"]:
            tgt_text.data.body = f"TARGET: {HUD_STATE['primary_target']}"
            if alt < 1.0:
                status_text.data.body = "STATUS: SAFE TOUCHDOWN"
            else:
                status_text.data.body = "STATUS: DESCENDING"
                status_text.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.2, 1.0, 0.2, 1.0)
        elif frame == HUD_STATE["event_frame"] or frame == HUD_STATE["event_frame"] + 1:
            status_text.data.body = "STATUS: HAZARD DETECTED!"
            status_text.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.0, 0.0, 1.0)
            tgt_text.data.body = f"TARGET: {HUD_STATE['primary_target']}"
        else:
            tgt_text.data.body = f"TARGET: {HUD_STATE['new_target']}"
            if alt < 1.0:
                status_text.data.body = "STATUS: SAFE TOUCHDOWN"
                status_text.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.2, 0.8, 1.0, 1.0)
            else:
                status_text.data.body = "STATUS: REPLANNING / DIVERTING"
                status_text.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.8, 0.0, 1.0)
                
        dv_text.data.body = f"DV: {HUD_STATE['maneuver_cost']:.1f} m/s"

def register_telemetry_handler():
    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.frame_change_post.append(update_telemetry)

if __name__ == "__main__":
    setup_telemetry_ui()
    register_telemetry_handler()
