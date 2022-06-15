bl_info = {
    "name": "RigTools",
    "blender": (3, 0, 0),
    "author": "ScottVMariotte",
    "version": (0, 0, 1),
    "category": "Rigging"
}

if "bpy" in locals():
    import importlib
    importlib.reload(blender_ops)
    importlib.reload(tools)
    importlib.reload(ui)

else:
    import bpy
    from . import blender_ops
    from . import tools
    from . import ui

classes = ui.classes.copy()
classes.add(ui.RT_PT_RigTools)
classes.add(ui.RigTPreferences)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
