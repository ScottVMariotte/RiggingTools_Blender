import bpy
import mathutils
import math
import bmesh
import re

from . tools import *

# TODO: Follow blender addon Style Conventions

class Mod_Constraint_Space(bpy.types.Operator):
    bl_idname = "armature.mod_constraints_space"
    bl_label = "mod constraints space"
    bl_description = "Allows enable/disable of all selected bones."

    def getConstraints(self, context):
        tuples = [("No Filter", "No Filter", "No Filter")]
        [tuples.append(constraint)
         for constraint in ConstraintInfo.getConstraints()]
        return tuples

    def getOwnerSpaces(self, context):
        tuples = [("No Change", "No Change", "No Change")]
        [tuples.append(space) for space in ConstraintInfo.getOwnerSpaces()]
        return tuples

    def getTargetSpaces(self, context):
        tuples = [("No Change", "No Change", "No Change")]
        [tuples.append(space) for space in ConstraintInfo.getTargetSpaces()]
        return tuples

    constraintFilter: bpy.props.EnumProperty(
        items=getConstraints, name='Filter', description="Choose sconstraint type to affect")
    targetSpace: bpy.props.EnumProperty(
        items=getTargetSpaces, name='Target Space', description="Choose space here")
    ownerSpace: bpy.props.EnumProperty(
        items=getOwnerSpaces, name='Owner Space', description="Choose space here")

    @ classmethod
    def poll(cls, context):
        return Poll.check_poll(activeType="ARMATURE", activeMode="POSE", minBones=1)

    def execute(self, context):
        selected = context.selected_pose_bones

        for bone in selected:
            for constraint in bone.constraints:
                if(constraint.name == self.constraintFilter or self.constraintFilter == "No Filter"):
                    constraint.target_space = constraint.target_space if self.targetSpace == "No Change" else self.targetSpace
                    constraint.owner_space = constraint.owner_space if self.ownerSpace == "No Change" else self.ownerSpace

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Toggle_Constraints(bpy.types.Operator):
    bl_idname = "armature.toggle_constraints"
    bl_label = "toggle constraints"
    bl_description = "Allows enable/disable of all selected bones."

    Toggle: bpy.props.BoolProperty(name="On?")

    @ classmethod
    def poll(cls, context):
        return Poll.check_poll(activeType="ARMATURE", activeMode="POSE", numObjs=1)

    def execute(self, context):
        selected = context.selected_pose_bones
        for bone in selected:
            for constraint in bone.constraints:
                constraint.enabled = self.Toggle
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Remove_Constraints(bpy.types.Operator):
    bl_idname = "armature.remove_constraints"
    bl_label = "remove constraints"
    bl_description = "Removes constraints from all selected bones."

    @ classmethod
    def poll(cls, context):
        return Poll.check_poll(activeType="ARMATURE", activeMode="POSE", numObjs=1)

    def execute(self, context):
        selected = context.selected_pose_bones
        for bone in selected:
            for constraint in bone.constraints:
                bone.constraints.remove(constraint)
        return {"FINISHED"}


class Add_Many_Constraints(bpy.types.Operator):
    bl_idname = "armature.add_many_constraints"
    bl_label = "add Many constraints"
    bl_description = "Adds constraints to selected bones with target as active bone."

    def getConstraintTuples(self, context):
        return ConstraintInfo.getConstraints()

    influence: bpy.props.FloatProperty(name="influence")
    selectedConstraint: bpy.props.EnumProperty(
        items=getConstraintTuples, name='Select Constraint', description="Choose constraint here")

    @ classmethod
    def poll(cls, context):
        return (Poll.check_poll(activeType="ARMATURE", activeMode="POSE", numObjs=1) and
                len(context.selected_pose_bones) > 2)

    def execute(self, context):
        armature = context.active_object

        bpy.ops.object.mode_set(mode='EDIT')
        active = armature.data.edit_bones.active.name
        bpy.ops.object.mode_set(mode='POSE')

        selected = context.selected_pose_bones
        for bone in selected:
            if(bone.name != active):
                constraint = bone.constraints.new(self.selectedConstraint)
                constraint.target = armature
                constraint.subtarget = active
                constraint.influence = self.influence

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Add_Twist_Constraints(bpy.types.Operator):
    bl_idname = "armature.add_twist_onstraints"
    bl_label = "Add Twist Constraints"
    bl_description = "Adds twist to selected bones with active as target."
    fromHead: bpy.props.BoolProperty(name="From Head?")

    @ classmethod
    def poll(cls, context):
        return Poll.check_poll(activeType="ARMATURE", activeMode="POSE")

    def execute(self, context):
        initMode = context.active_object.mode

        bpy.ops.object.mode_set(mode='EDIT')
        sets = ArmatureTools.get_contiguous_sets(
            context.selected_editable_bones)
        unconnected = len(sets) == len(context.selected_editable_bones)

        # get sorted set of bones and remove active. loop through set and add constrains with active target
        bones = [bone.name for bone in context.selected_editable_bones]
        active = context.active_object.data.edit_bones.active.name
        bones.remove(active)

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = context.active_object.pose.bones

        for i in range(len(bones)):
            bone = poseBones[poseBones.find(bones[i])]

            constraint = bone.constraints.new("COPY_ROTATION")
            constraint.target = context.active_object
            constraint.target_space = "LOCAL"
            constraint.owner_space = "LOCAL"
            constraint.subtarget = active
            constraint.use_x = False
            constraint.use_z = False

            if(unconnected):
                subIndex = ((self.fromHead * ((len(bones)) - i))) + \
                    ((not self.fromHead) * (i + 1))
                constraint.influence = subIndex * ((1/(len(bones)+1)))
            else:
                val = (1/(len(bones)+1))
                if(self.fromHead):
                    constraint.invert_y = i != 0
                    constraint.influence = val if i != 0 else 1 - val
                else:
                    constraint.influence = val

        bpy.ops.object.mode_set(mode=initMode)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

#
# Bone Generation
#


class Subdivide_Bones(bpy.types.Operator):
    bl_idname = "armature.subdivide_bones"
    bl_label = "Subdivide Bones"
    bl_description = "Subdivide Bones with a naming order that starts at head bone"

    @classmethod
    def poll(self, context):
        return Poll.check_poll(activeType="ARMATURE", activeMode="EDIT") and len(context.selected_editable_bones) > 0

    #
    # Go back over this and clean/optimize
    #
    def execute(self, context):
        bpy.ops.armature.subdivide()
        bones = context.selected_editable_bones

        allBones = {}
        for bone in context.active_object.data.edit_bones:
            allBones[bone.name] = bone

        uniqueBones = {}
        for bone in bones:
            name = Naming.split(bone.name)
            name = name[0] + name[2]
            if(name not in uniqueBones):
                head = bone
                if(name not in uniqueBones):
                    while(head.parent in bones and Naming.compare_names(head.parent.name, name, trim1=True)):
                        head = head.parent
                uniqueBones[name] = head

        RigRename = 1111
        for key in uniqueBones:
            bone = uniqueBones[key]
            children = bone.children
            bone.name = Naming.rename(bone.name)
            count = int('0' + Naming.split(bone.name)[1])
            while(True):
                count += 1
                bone = children[0]
                children = bone.children
                split = Naming.split(bone.name)
                if(split[0] + split[2] != key):
                    break

                newName = split[0] + "." + str(count).zfill(3) + split[2]
                if(newName in allBones):
                    allBones[newName].name += "." + str(RigRename)
                    RigRename += 1

                if(bone.name in allBones):
                    del allBones[bone.name]

                bone.name = newName

                if(len(bone.children) == 0):
                    break
                check = Naming.split(bone.name)
                check = check[0] + check[2]
                if(check != key):
                    break

        return {"FINISHED"}


class Gen_Bone_Copies(bpy.types.Operator):
    bl_idname = "armature.gen_bone_copies"
    bl_label = "Gen Bone Copies"
    bl_description = "Generates copies of bones with new prefixes. Can replace existing prefixes"

    prefix: bpy.props.StringProperty(name="Preffix")
    replace: bpy.props.StringProperty(name="Replace")
    startLayer: bpy.props.IntProperty(name="StartLayer")

    @classmethod
    def poll(self, context):
        return Poll.check_poll(activeType="ARMATURE", activeMode="EDIT", minBones=1)

    def execute(self, context):
        eidit_bones = context.active_object.data.edit_bones
        bones = context.selected_editable_bones
        names = [bone.name for bone in bones]

        for bone in bones:
            bone.select = False

        prefixs = self.prefix.split(",")
        layer = self.startLayer
        layers = [False for i in range(32)]
        layers[layer] = True
        for prfx in prefixs:
            newNames = []
            if self.replace == "":
                newNames = [Naming.gen_new(name, prefix=prfx)
                            for name in names]
            else:
                for name in names:
                    newNames.append(name.replace(self.replace, prfx))

            newBones = []
            for i in range(len(newNames)):
                refBone = bones[i]

                newBone = eidit_bones.new(newNames[i])

                newBone.head = refBone.head
                newBone.tail = refBone.tail
                newBone.roll = refBone.roll
                newBone.select = True
                newBones.append(newBone)

            bpy.ops.armature.bone_layers(layers=layers)
            layer += 1
            layers[layer-1] = False
            layers[layer] = True

            for i in range(len(newNames)):
                refBone = bones[i]
                newBone = newBones[i]
                newBone.select = False

                refParentIndex = names.index(
                    refBone.parent.name) if refBone.parent is not None and refBone.parent.name in names else -1
                if(refParentIndex == -1):
                    continue
                newBone.parent = newBones[refParentIndex]
                newBone.use_connect = refBone.use_connect

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Gen_Eye_Bones(bpy.types.Operator):
    bl_idname = "armature.gen_eye_bones"
    bl_label = "Gen Eye Bones"
    bl_description = "Generates eye bones based on points selected in mesh edit mode"

    @classmethod
    def poll(cls, context):
        checkObjects = Poll.check_poll(
            types="ARMATURE,MESH", activeType="MESH", activeMode="EDIT", numObjs=2)
        if(checkObjects):
            count = 0
            for v in bpy.context.active_object.data.vertices:
                count += v.select
                if(count > 2):
                    return True
        return False

    def execute(self, context):
        # Blender version is 2.Required when 73 or above
        if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 73:
            bm.verts.ensure_lookup_table()

        objMesh = context.active_object
        objArmature = None
        for obj in context.selected_editable_objects:
            if obj is not objMesh:
                objArmature = obj
        initMode = objArmature.mode

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(objMesh.data)

        bpy.ops.view3d.snap_cursor_to_selected()
        locEyeCenter = bpy.context.scene.cursor.location
        locEyePupil = bm.select_history[len(
            bm.select_history)-1].co  # last selected vertex

        # switch active to armature
        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = objArmature
        bpy.ops.object.mode_set(mode='EDIT')
        editBones = objArmature.data.edit_bones

        # UPDATE THIS NAMING SECTION
        eyeName = "Eye"
        upperName = "Eye_UpperLid"
        lowerName = "Eye_LowerLid"
        boneEye = editBones.new("Eye")
        boneLidU = editBones.new(upperName)
        boneLidD = editBones.new(lowerName)

        boneEye.head = locEyeCenter
        boneEye.tail = locEyePupil

        boneLidU.head = locEyeCenter
        boneLidU.tail = locEyePupil

        boneLidD.head = locEyeCenter
        boneLidD.tail = locEyePupil

        x, y, z = boneEye.matrix.to_3x3().col

        mat = (mathutils.Matrix.Translation(boneEye.head) @
               mathutils.Matrix.Rotation(math.radians(-10), 4, x) @
               mathutils.Matrix.Translation(-boneEye.head)
               )

        boneLidD.transform(mat)

        mat = (mathutils.Matrix.Translation(boneEye.head) @
               mathutils.Matrix.Rotation(math.radians(10), 4, x) @
               mathutils.Matrix.Translation(-boneEye.head)
               )

        boneLidU.transform(mat)

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = objArmature.pose.bones

        upperPose = poseBones[poseBones.find(upperName)]
        lowerPose = poseBones[poseBones.find(lowerName)]

        constraint = upperPose.constraints.new('COPY_ROTATION')
        constraint.target = objArmature
        constraint.subtarget = eyeName
        constraint.target_space = "LOCAL"
        constraint.owner_space = "LOCAL"
        constraint.influence = .5

        constraint = lowerPose.constraints.new('COPY_ROTATION')
        constraint.target = objArmature
        constraint.subtarget = eyeName
        constraint.target_space = "LOCAL"
        constraint.owner_space = "LOCAL"
        constraint.influence = .5

        bpy.ops.object.mode_set(mode=initMode)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Gen_Constrain_Bones(bpy.types.Operator):
    bl_idname = "armature.gen_constrain_bones"
    bl_label = "Gen Constrain Bones"
    bl_description = "Gen bones that selected bones are constrained to"

    # returns tuples for the list UI
    def getNumBones(self, context):
        bones = context.selected_editable_bones if context.active_object.mode == "EDIT" else context.selected_pose_bones
        tups = []

        lsFactors = SimpleMaths.find_factors(len(bones))
        for i in range(len(lsFactors)):
            s = str(lsFactors[i])
            tups.append((s, s, "Num Bones"))

        return tups

    prefix: bpy.props.StringProperty(name="Preffix")
    suffix: bpy.props.StringProperty(name="Suffix")

    removeParents: bpy.props.BoolProperty(name="Remove Parents?")
    numBones: bpy.props.EnumProperty(
        items=getNumBones, name='Num Bones', description="Choose object here")

    @classmethod
    def poll(cls, context):
        return (Poll.check_poll(activeType="ARMATURE", activeMode="EDIT") and
                len(context.selected_editable_bones) > 0 and
                ArmatureTools.is_contiguous_branchless(
                    context.selected_editable_bones)
                )

    def execute(self, context):
        objArmature = context.active_object
        initMode = objArmature.mode
        bpy.ops.object.mode_set(mode='EDIT')

        selectedBones = context.selected_editable_bones
        numNewBones = int(self.numBones)
        offset = int(len(selectedBones) / numNewBones)

        connected = ArmatureTools.is_contiguous_branchless(selectedBones)
        selectedBones = ArmatureTools.get_sorted(
            selectedBones) if connected else selectedBones
        points = PointTools.gen_points_from_bones(selectedBones, offset=offset)

        selectedNames = [bone.name for bone in selectedBones]

        count = -1
        rolls = []
        newNames = []
        base = Naming.trim_name(selectedNames[0])
        for i in range(0, numNewBones):
            offIndex = offset * i

            name = Naming.trim_name(selectedNames[offIndex])

            if(name == base):
                count += 1
            else:
                count = 0
                base = name

            newNames.append(Naming.gen_new(
                name, prefix=self.prefix, suffix=self.suffix, count=count))
            rolls.append(selectedBones[offIndex].roll)

        editBones = objArmature.data.edit_bones

        newBones = ArmatureTools.gen_bones_along_points(
            editBones, points, newNames, rolls=rolls)

        if(self.removeParents):
            for bone in selectedBones:
                bone.parent = None

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = objArmature.pose.bones
        for i in range(numNewBones):
            offIndex = offset * i
            boneTarget = newNames[i]
            numRange = ((offset-1) * (self.removeParents)) + 1
            for j in range(numRange):
                boneConstrained = poseBones[poseBones.find(
                    selectedNames[offIndex + j])]
                constraint = boneConstrained.constraints.new('COPY_TRANSFORMS')
                constraint.target = objArmature
                constraint.subtarget = boneTarget
                constraint.head_tail = (j * (1/(numRange)))

        bpy.ops.object.mode_set(mode=initMode)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Snap_Bones_to_Curve(bpy.types.Operator):
    bl_idname = "armature.snap_bones_curve"
    bl_label = "Snap Bones To Curve"
    bl_description = "Creates a chain of stretchy Bones with ctrl bones"

    options = [("Even", "Even", ""), ("Closest", "Closest Points", "")]
    # options = [("Closest","Closest Points","")]

    snapType: bpy.props.EnumProperty(
        items=options, name='Snap Type', description="How the bones should snap to curve")

    @classmethod
    def poll(cls, context):
        return (Poll.check_poll(types="ARMATURE,CURVE", activeType="ARMATURE", activeMode="EDIT", numObjs=2) and
                len(context.selected_editable_bones) > 0)

    def execute(self, context):
        objArmature = context.active_object
        objCurve = None
        for obj in context.selected_editable_objects:
            if obj is not objArmature:
                objCurve = obj
        bones = context.selected_editable_bones

        # each spline is a separate curve in the object
        spline = objCurve.data.splines[0]
        # bPoints represent the handles of the curve. two bPoints make a segment
        bPoints = BezierPoint.copyList(spline.bezier_points)

        numCurveSegments = len(bPoints) - 1
        # number of points per segment
        resolution = int(len(bones) / numCurveSegments)

        PointTools.bPoints_translate_space(bPoints, objCurve, objArmature)

        # Snaps bones evenly along the curve
        if(self.snapType == "Even"):
            points = PointTools.gen_points_from_bPoints(
                bPoints, resolution, evenDistribution=True)
            ArmatureTools.snap_bones_to_points(bones, points)

        # Snaps bones to closest curve point
        else:
            # use a sparse and dense curve to estimate the closest point along the curve
            # search through sparce point distribution then map into dense point distribution

            precision = .01
            sparseResolution = 20

            sparsePoints = PointTools.gen_points_from_bPoints(
                bPoints, sparseResolution, evenDistribution=True)
            # use sparse points to calculate total curve length
            curveLength = PointTools.get_length_points(sparsePoints)

            # Use curveLength to create new resolutions for the sparse and dence curves
            sparseResolution = int(curveLength / (precision * 10))
            denseResolution = int(curveLength / precision)

            # get the points along each curve
            sparsePoints = PointTools.gen_points_from_bPoints(
                bPoints, sparseResolution, evenDistribution=True)
            densePoints = PointTools.gen_points_from_bPoints(
                bPoints, denseResolution, evenDistribution=True)
            bonePoints = PointTools.gen_points_from_bones(
                bones)  # points that represent bones

            # update resolutions to hold length of points list
            sparseResolution = int(sparseResolution * numCurveSegments)
            denseResolution = int(denseResolution * numCurveSegments)
            # used to map sparse index to dence index
            resolutionRatio = denseResolution/sparseResolution

            for i in range(len(bonePoints)):
                point = bonePoints[i]

                index = -1
                closest = 999999999999
                for j in range(0, sparseResolution):
                    distance = math.dist(point, sparsePoints[j])
                    if(distance < closest):
                        index = j
                        closest = distance

                # how many time we have changed direction (loop stops at 2)
                flop = 0
                delta = 1  # direction we are iterating (1 or -1)
                doFlop = False  # change "direction" we are iterating
                index = int(index * resolutionRatio)  # start index
                inRage = ((delta + index) >=
                          0) and ((delta + index) < denseResolution)

                while(flop < 2 and inRage):  # make this more readable
                    distance = math.dist(point, densePoints[index])
                    index += delta
                    distanceDelta = math.dist(point, densePoints[index])

                    doFlop = distanceDelta > distance
                    delta = (doFlop * (-1 * delta)) + ((not doFlop) * delta)

                    inRage = ((delta + index) >=
                              0) and ((delta + index) < denseResolution)
                    flop += doFlop

                bonePoints[i] = densePoints[index+delta]

            ArmatureTools.snap_bones_to_points(bones, bonePoints)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class Gen_Bone_Chain_From_Bones(bpy.types.Operator):
    bl_idname = "armature.gen_bone_chain_from_bones"
    bl_label = "bone Chain From Bones"
    bl_description = "Creates a chain of stretchy Bones with ctrl bones"

    def __init__(self):
        self.prefix = "CTRL_"

    def getAxisTuples(self, context):
        constraints = ['X', 'Z', '-X', '-Z']

        tuples = []
        for constraint in constraints:
            tuples.append((constraint, constraint, constraint))

        return tuples

    prefix: bpy.props.StringProperty(name="Preffix")
    suffix: bpy.props.StringProperty(name="Suffix")
    axis: bpy.props.EnumProperty(
        items=getAxisTuples, name='Axis', description="Choose Axis")

    avgDir: bpy.props.BoolProperty(name="AvgDirections?")

    @classmethod
    def poll(cls, context):
        return (Poll.check_poll(activeType="ARMATURE", activeMode="EDIT") and
                len(context.selected_editable_bones) > 0 and
                ArmatureTools.is_contiguous_branchless(context.selected_editable_bones))

    def execute(self, context):
        objArmature = context.active_object
        initMode = objArmature.mode

        bpy.ops.object.mode_set(mode='EDIT')
        selected = ArmatureTools.get_sorted(
            context.selected_editable_bones)  # sort selected bones

        name = re.sub(r'\d+', '', selected[0].name)
        if(name[-1] == "."):
            name = name[0:-1]

        directions = []
        for bone in selected:
            axis = bone.x_axis
            if(self.axis == "X"):
                axis = bone.x_axis
            elif(self.axis == "-X"):
                axis = bone.x_axis * -1
            elif(self.axis == "Z"):
                axis = bone.z_axis
            elif(self.axis == "-Z"):
                axis = bone.z_axis * -1
            else:
                return {"CANCELLED"}

            directions.append(axis)
            if(bone == selected[-1]):
                directions.append(axis)

        points = PointTools.gen_points_from_bones(
            selected)  # gen points from selected
        points = PointTools.gen_points_tangent_to_points(
            points, directions, 1.0, includeOriginal=True, avrageDirections=self.avgDir)  # generate new bones off points

        selectedNames = [bone.name for bone in selected]
        baseName = Naming.trim_name(selectedNames[0])
        ctrlNames = [Naming.gen_new(baseName, prefix=self.prefix, suffix=self.suffix, count=i)
                     for i in range(len(selectedNames) + 1)]
        ArmatureTools.gen_bones_along_points(
            objArmature.data.edit_bones, points, ctrlNames, parents=False, useConnect=False, offset=2)

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = objArmature.pose.bones
        for i in range(len(selectedNames)):
            # retrieve pose bone
            bone = poseBones[poseBones.find(selectedNames[i])]
            # Constraint targets
            ctrlH = ctrlNames[i]
            ctrlT = ctrlNames[i+1]

            constraint = bone.constraints.new('COPY_LOCATION')
            constraint.subtarget = ctrlH
            constraint.target = objArmature

            constraint = bone.constraints.new('STRETCH_TO')
            constraint.subtarget = ctrlT
            constraint.target = objArmature

        bpy.ops.object.mode_set(mode=initMode)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

# TODO: allow for controll of roll/axis direction


class Gen_Bone_Curve(bpy.types.Operator):
    bl_idname = "armature.bone_curve"
    bl_label = "bone curve"
    bl_description = "Creates a chain of Bones along a bezier curve"

    def __init__(self):
        context = bpy.context

        self.numObjs = len(context.selected_objects)
        self.chainName = "BoneChain"
        self.numBones = 10
        self.connected = False

    chainName: bpy.props.StringProperty(name="Name of chain")
    prefix: bpy.props.StringProperty(name="prefix")
    suffix: bpy.props.StringProperty(name="Suffix")
    even: bpy.props.BoolProperty(name="even distribution?")

    @classmethod
    def poll(cls, context):
        return Poll.check_poll(types="ARMATURE,CURVE", activeType="ARMATURE", activeMode="EDIT", numObjs=2)

    def execute(self, context):
        objCurve = None
        objArmature = context.active_object
        bpy.ops.object.mode_set(mode="OBJECT")
        for obj in context.selected_objects:
            if obj is not objArmature:
                objCurve = obj

        bpy.ops.object.mode_set(mode="EDIT")

        # get curve information
        # each spline is a separate curve in the object
        spline = objCurve.data.splines[0]
        # bPoints represent the handles of the curve
        bPoints = BezierPoint.copyList(spline.bezier_points)
        resolution = spline.resolution_u  # number of points per segment
        curveSegments = len(bPoints) - 1

        # transformation information from both both objects
        PointTools.bPoints_translate_space(bPoints, objCurve, objArmature)

        curvePoints = PointTools.gen_points_from_bPoints(
            bPoints, resolution, evenDistribution=self.even)

        names = [Naming.gen_new(self.name, prefix=self.prefix, suffix=self.suffix, count=i)
                 for i in range(len(curvePoints)-1)]
        ArmatureTools.gen_bones_along_points(
            objArmature.data.edit_bones, curvePoints, names)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
