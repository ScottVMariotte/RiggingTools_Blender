#
#TODO: UI : Make a basic UI
#

bl_info = {
    "name" : "RigTools",
    "blender": (3,0, 0),
    "author" : "ScottVMariotte",
    "version" : (0,0,1),
    "category" : "Rigging"
}

# Check if this add-on is being reloaded
if "bpy" not in locals():
    from . import blender_ops
    from . import tools
else:
    import importlib
    
    importlib.reload(blender_ops)
    importlib.reload(tools)

import bpy

classes = { blender_ops.Gen_Bone_Curve,
            blender_ops.Gen_Bone_Chain,
            blender_ops.Snap_Bones_to_Curve,
            blender_ops.Gen_Constrain_Bones,
            blender_ops.Gen_Eye_Bones,
            blender_ops.Add_Twist_Constraints,
            blender_ops.Remove_Constraints,
            blender_ops.Add_Many_Constraints,
            blender_ops.Toggle_Constraints,
            blender_ops.Gen_Bone_Chain_From_Bones,
            blender_ops.Gen_Bone_Copies
            }

def register():
    #print("Registor classes")
    for c in classes:
        #print("Registoring - " + str(c))
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    