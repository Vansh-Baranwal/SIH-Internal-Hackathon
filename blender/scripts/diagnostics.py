import bpy

print("\n--- DIAGNOSTICS ---")
lander = bpy.data.objects.get("Lander")
if lander:
    print(f"VIKRAM OBJECT: {lander.name}")
    print(f"PARENT: {lander.parent.name if lander.parent else 'None'}")
    print(f"TYPE: {lander.type}")
    print(f"CHILDREN: {len(lander.children)}")
    
    action = None
    if lander.animation_data:
        action = lander.animation_data.action
        
    print(f"ACTION: {action.name if action else 'None'}")
    
    if action:
        # In newer Blender, checking if there are keyframes
        # We can just check action directly or lander's fcurves
        try:
            print(f"FCURVES: {len(action.fcurves)}")
            loc_fcurves = [fc for fc in action.fcurves if fc.data_path == 'location']
            if loc_fcurves:
                kf_points = loc_fcurves[0].keyframe_points
                print(f"KEYFRAMES: {len(kf_points)}")
                print(f"LOCATION KEYFRAME RANGE: {kf_points[0].co[0]} -> {kf_points[-1].co[0]}")
                print(f"FIRST LOCATION Z: {kf_points[0].co[1]}")
                print(f"LAST LOCATION Z: {kf_points[-1].co[1]}")
            else:
                print("KEYFRAMES: 0 location fcurves")
        except AttributeError:
            print("KEYFRAMES: (AttributeError - Action has no fcurves in this Blender version)")
            # Try to get fcurves from object?
            print("Location keys exist? ", end="")
            try:
                print(bool(lander.animation_data.action))
            except:
                pass
    else:
        print("KEYFRAMES: None")
else:
    print("VIKRAM OBJECT: NOT FOUND")

print("--- END DIAGNOSTICS ---\n")
