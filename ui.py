import bpy
from . import blender_ops

classes = {blender_ops.GenBoneCurve,
           blender_ops.SnapBonestoCurve,
           blender_ops.GenConstrainBones,
           blender_ops.GenEyeBones,
           blender_ops.AddTwistConstraints,
           blender_ops.RemoveConstraints,
           blender_ops.AddManyConstraints,
           blender_ops.ToggleConstraints,
           blender_ops.GenBoneChainFromBones,
           blender_ops.GenBoneCopies,
           blender_ops.SubdivideBones,
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
