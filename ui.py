import bpy
from . import blender_ops

classes = {blender_ops.Gen_Bone_Curve,
           blender_ops.Snap_Bones_to_Curve,
           blender_ops.Gen_Constrain_Bones,
           blender_ops.Gen_Eye_Bones,
           blender_ops.Add_Twist_Constraints,
           blender_ops.Remove_Constraints,
           blender_ops.Add_Many_Constraints,
           blender_ops.Toggle_Constraints,
           blender_ops.Gen_Bone_Chain_From_Bones,
           blender_ops.Gen_Bone_Copies,
           blender_ops.Subdivide_Bones,
           blender_ops.Mod_Constraint_Space,
           blender_ops.MergeParentByDistance
           }


class RT_PT_RigTools(bpy.types.Panel):
    bl_idname = 'RT_PT_RigTools'
    bl_label = 'RigTools Operations'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @ classmethod
    def poll(cls, context):
        return context.preferences.addons[__package__].preferences.panelToggle

    def draw(self, context):
        col = self.layout.column()
        for operation in classes:
            col.operator(operation.bl_idname, text=operation.bl_label)


class RigTPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    panelToggle: bpy.props.BoolProperty(name="Panel Toggle")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "panelToggle")
