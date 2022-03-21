import bpy
import mathutils
import math
import bmesh
import re

from . tools import *

#TODO: Operators : Constraint Programming
#CLEAN : ... more intuitive and cohesive naming,  cohesive poll methods

class Toggle_Constraints(bpy.types.Operator):
    bl_idname = "armature.toggle_constraints"
    bl_label = "toggle constraints"
    bl_description = "Allows enable/disable of all selected bones."
    
    Toggle: bpy.props.BoolProperty(name="On?")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and 
                context.active_object.type == "ARMATURE" and
                context.active_object.mode == "POSE" and
                len(context.selected_pose_bones) > 0)
    
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
    
    @classmethod
    def poll(cls, context):
        return (context.active_object != None and 
                context.active_object.type == "ARMATURE" and 
                context.active_object.mode == "POSE" and 
                len(context.selected_pose_bones) > 0)

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
        constraints = ['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE', 'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'TRANSFORM', 'CLAMP_TO', 'DAMPED_TRACK', 'LOCKED_TRACK', 'STRETCH_TO', 'TRACK_TO', 'CHILD_OF']

        tuples = [] 
        for constraint in constraints:
            tuples.append((constraint,constraint,constraint))

        return tuples

    influence: bpy.props.FloatProperty(name="influence")
    selectedConstraint: bpy.props.EnumProperty(items=getConstraintTuples, name='Select Constraint', description = "Choose constraint here")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and 
                context.active_object.type == "ARMATURE" and 
                context.active_object.mode == "POSE" and 
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
    
    def __init__(self):
        context = bpy.context

    fromHead: bpy.props.BoolProperty(name="From Head?")
    
    @classmethod
    def poll(cls, context):
        objActive = context.active_object
        if(objActive != None and objActive.type == "ARMATURE" and objActive.mode != "OBJECT"):
            bones = context.selected_editable_bones if objActive.mode == "EDIT" else context.selected_pose_bones
            sets = ArmatureTools.get_contiguous_sets(bones)
            numSets = len(sets)
            
            return numSets == len(bones) or (numSets == 2) 
        return False

    def execute(self, context):
        initMode = context.active_object.mode

        bpy.ops.object.mode_set(mode='EDIT')
        sets = ArmatureTools.get_contiguous_sets(context.selected_editable_bones)
        unconnected = len(sets) == len(context.selected_editable_bones)

        #get sorted set of bones and remove active. loop through set and add constrains with active target
        bones = ArmatureTools.get_bone_names(context.selected_editable_bones)
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
                subIndex = ((self.fromHead * ((len(bones)) - i))) + ((not self.fromHead) * (i + 1))
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

class Gen_Eye_Bones(bpy.types.Operator):
    bl_idname = "armature.gen_eye_bones"
    bl_label = "Gen Eye Bones"
    bl_description = "Generates eye bones based on points selected in mesh edit mode"

    def __init__(self):
        context = bpy.context
        numObjs = len(context.selected_objects)
        if(numObjs != 2): return False
        
        self.objMesh = None
        self.objArmature = None
        for i in range(numObjs):
            obj = context.selected_objects[i]
            if(obj.type == "MESH"):
                self.objMesh = obj
            else:
                self.objArmature = obj

    @classmethod
    def poll(cls, context):
        numObjs = len(context.selected_objects)
        if(len(context.selected_objects) != 2): 
            return False
        
        meshSelected = False
        armatureSelected = False
        for i in range(numObjs):
            obj = context.selected_objects[i]
            meshSelected = meshSelected or obj.type == "MESH"
            armatureSelected = armatureSelected or obj.type == "ARMATURE"
        
        if(not meshSelected or not armatureSelected or bpy.context.active_object.type != "MESH"):
            return False

        selectedVerts = []
        for v in bpy.context.active_object.data.vertices:
            if v.select:
                selectedVerts.append(v)

        return meshSelected and armatureSelected and self.objMesh.data and len(selectedVerts > 1)

    def execute(self, context):
        #Blender version is 2.Required when 73 or above
        if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 73:
            bm.verts.ensure_lookup_table()

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(self.objMesh.data)

        bpy.ops.view3d.snap_cursor_to_selected()
        locEyeCenter = bpy.context.scene.cursor.location
        locEyePupil = bm.select_history[len(bm.select_history)-1].co#last selected vertex
        
        #switch active to armature
        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = self.objArmature
        bpy.ops.object.mode_set(mode='EDIT')
        editBones = self.objArmature.data.edit_bones

        #UPDATE THIS NAMING SECTION
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

        x,y,z = boneEye.matrix.to_3x3().col

        mat = (mathutils.Matrix.Translation(boneEye.head) @
            mathutils.Matrix.Rotation(math.radians(-10), 4, x) @
            mathutils.Matrix.Translation(-boneEye.head)
        )

        boneLidD.transform(mat)
        mat.transpose()
        boneLidU.transform(mat)

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = self.objArmature.pose.bones

        upperPose = poseBones[poseBones.find(upperName)]
        lowerPose = poseBones[poseBones.find(lowerName)]

        constraint = upperPose.constraints.new('COPY_ROTATION')
        constraint.target = self.objArmature
        constraint.subtarget = eyeName
        constraint.target_space = "LOCAL"
        constraint.owner_space = "LOCAL"
        constraint.influence = .5

        constraint = lowerPose.constraints.new('COPY_ROTATION')
        constraint.target = self.objArmature
        constraint.subtarget = eyeName
        constraint.target_space = "LOCAL"
        constraint.owner_space = "LOCAL"
        constraint.influence = .5

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class Gen_Constrain_Bones(bpy.types.Operator):
    bl_idname = "armature.gen_constrain_bones"
    bl_label = "Gen Constrain Bones"
    bl_description = "Gen bones that selected bones are constrained to"

    #returns tuples for the list UI 
    def getNumBones(self, context):
        bones = context.selected_editable_bones if context.active_object.mode == "EDIT" else context.selected_pose_bones
        tups =[]
        
        lsFactors = SimpleMaths.find_factors(len(bones))
        for i in range(len(lsFactors)):
            s = str(lsFactors[i])
            tups.append((s,s,"Num Bones"))
        
        return tups

    def __init__(self):
        context = bpy.context
        self.objArmature = context.active_object
        self.initMode = self.objArmature.mode

    prefix: bpy.props.StringProperty(name="Preffix")
    suffix: bpy.props.StringProperty(name="Suffix")

    numBones: bpy.props.EnumProperty(items=getNumBones, name='Num Bones', description = "Choose object here")

    @classmethod
    def poll(cls, context):
        objArmature = context.active_object
        if(objArmature == None or objArmature.type != "ARMATURE" or objArmature.mode == "OBJECT"): 
            return False

        numBones = len(context.selected_editable_bones) if objArmature.mode == "EDIT" else len(context.selected_pose_bones)
        return numBones > 0

    def execute(self, context):
        initMode = self.objArmature.mode
        bpy.ops.object.mode_set(mode='EDIT')

        selectedBones = context.selected_editable_bones
        numNewBones = int(self.numBones)
        offset = int(len(selectedBones) / numNewBones)

        #Sort selected (head to tail) bones and get the names
        connected = ArmatureTools.is_contiguous_branchless(selectedBones)
        selected = ArmatureTools.get_sorted(selectedBones) if connected else selectedBones
        
        points = PointTools.gen_points_from_bones(selected, offset = offset)
        selectedNames = ArmatureTools.get_bone_names(selected)
        
        rolls = []
        newNames = []
        for i in range(numNewBones):
            offIndex = offset * i
            newNames.append(ArmatureTools.trim_bone_name(selectedNames[offIndex]))
            rolls.append(selected[offIndex].roll)
        
        editBones = self.objArmature.data.edit_bones
        newBones = ArmatureTools.gen_bones_along_points(editBones, points, newNames, self.prefix, self.suffix, rolls = rolls)

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = self.objArmature.pose.bones
        for i in range(numNewBones):
            offIndex = offset * i

            boneTarget = newBones[i]
            for j in range(((offset-1) * (not connected)) + 1):
                boneConstrained = poseBones[poseBones.find(selectedNames[offIndex + j])]
                constraint = boneConstrained.constraints.new('COPY_TRANSFORMS')
                constraint.target = self.objArmature
                constraint.subtarget = boneTarget


        bpy.ops.object.mode_set(mode=initMode)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class Snap_Bones_to_Curve(bpy.types.Operator):
    bl_idname = "armature.snap_bones_curve"
    bl_label = "Snap Bones To Curve"
    bl_description = "Creates a chain of stretchy Bones with ctrl bones"

    def __init__(self):
        context = bpy.context
        
        self.objArmature = None
        self.objCurve = None
        
        for i in range(len(context.selected_objects)):
            obj = context.selected_objects[i]
            if(obj.type == "CURVE"):
                self.objCurve = obj
            elif(obj.type == "ARMATURE"):
                self.objArmature = obj

        self.bones = context.selected_editable_bones

    options = [("Even","Even",""),("Closest","Closest Points","")]

    snapType: bpy.props.EnumProperty(items=options, name='Snap Type', description = "How the bones should snap to curve")
    draw: bpy.props.BoolProperty(name='Draw')

    @classmethod
    def poll(cls, context):
        numObjs = len(context.selected_objects)
        if(numObjs != 2): 
            return False
        
        curve = False
        armature = False
        for i in range(numObjs):
            obj = context.selected_objects[i]
            curve = curve or obj.type == "CURVE"
            armature = armature or obj.type == "ARMATURE"
    
        return curve and armature and bpy.context.active_object.type  == "ARMATURE" and bpy.context.active_object.mode == "EDIT"

    def execute(self, context):
        spline = self.objCurve.data.splines[0]#each spline is a separate curve in the object
        bPoints = BezierPoint.copyList(spline.bezier_points)#bPoints represent the handles of the curve. two bPoints make a segment
        
        numCurveSegments = len(bPoints) - 1
        resolution = int(len(self.bones) / numCurveSegments)#number of points per segment

        #for i in range(len(bPoints)):#translate bPoints into armature space
        PointTools.bPoints_translate_space(bPoints, self.objCurve, self.objArmature)

        #Snaps bones evenly along the curve
        if(self.snapType == "Even"):
            points = PointTools.gen_points_from_bPoints(bPoints, resolution, evenDistribution = True)
            ArmatureTools.snap_bones_to_points(self.bones, points)

        #Snaps bones to closest curve point
        else:
            #use a sparse and dense curve to estimate the closest point along the curve
            #search through sparce point distribution then map into dense point distribution

            precision = .01
            sparseResolution = 20

            sparsePoints = PointTools.gen_points_from_bPoints(bPoints, sparseResolution, evenDistribution = True)
            curveLength = PointTools.get_length_points(sparsePoints)#use sparse points to calculate total curve length

            #Use curveLength to create new resolutions for the sparse and dence curves
            sparseResolution = int(curveLength / (precision * 10))
            denseResolution = int(curveLength / precision)

            #get the points along each curve
            sparsePoints = PointTools.gen_points_from_bPoints(bPoints, sparseResolution, evenDistribution = True)
            densePoints = PointTools.gen_points_from_bPoints(bPoints, denseResolution, evenDistribution = True)
            bonePoints = PointTools.gen_points_from_bPoints(self.bones)#points that represent bones
            
            #update resolutions to hold length of points list
            sparseResolution = int(sparseResolution * numCurveSegments)
            denseResolution = int(denseResolution * numCurveSegments)
            resolutionRatio = denseResolution/sparseResolution#used to map sparse index to dence index
            
            for i in range(len(bonePoints)):
                point = bonePoints[i]

                index = -1
                closest = 999999999999
                for j in range(0,sparseResolution):
                    distance = math.dist(point, sparsePoints[j])
                    if(distance < closest):
                        index = j
                        closest = distance

                flop = 0#how many time we have changed direction (loop stops at 2)
                delta = 1#direction we are iterating (1 or -1)
                doFlop = False#change "direction" we are iterating
                index =int(index * resolutionRatio)#start index
                inRage = ((delta + index) >= 0) and ((delta + index) < denseResolution)

                while(flop < 2 and inRage):#make this more readable
                    distance = math.dist(point, densePoints[index])
                    index += delta
                    distanceDelta = math.dist(point, densePoints[index])

                    doFlop = distanceDelta > distance
                    delta = (doFlop * (-1 * delta)) + ((not doFlop) * delta)
                    
                    inRage = ((delta + index) >= 0) and ((delta + index) < denseResolution)
                    flop += doFlop
                
                bonePoints[i] = densePoints[index+delta]

            ArmatureTools.snap_bones_to_points(self.bones, bonePoints)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class Gen_Bone_Chain_From_Bones(bpy.types.Operator):
    bl_idname = "armature.gen_bone_chain_from_bones"
    bl_label = "bone Chain From Bones"
    bl_description = "Creates a chain of stretchy Bones with ctrl bones"

    def __init__(self):
        context = bpy.context
        self.prefix = "CTRL_"

    def getAxisTuples(self, context):
        constraints = ['X', 'Z', '-X', '-Z']

        tuples = []
        for constraint in constraints:
            tuples.append((constraint,constraint,constraint))

        return tuples

    prefix: bpy.props.StringProperty(name="Preffix")
    axis: bpy.props.EnumProperty(items=getAxisTuples, name='Axis', description = "Choose Axis")

    @classmethod
    def poll(cls, context):
        if(context.active_object == None): 
            return False

        armature = context.active_object
        if(armature.type == "ARMATURE" and armature.mode != "OBJECT"):

            selected = context.selected_editable_bones if armature.mode == "EDIT" else context.selected_pose_bones
            contiguos = ArmatureTools.is_contiguous_branchless(selected)

            return len(selected) > 0 and contiguos

    def execute(self, context):
        objArmature = context.active_object
        initMode = objArmature.mode

        bpy.ops.object.mode_set(mode='EDIT')
        selected = ArmatureTools.get_sorted(context.selected_editable_bones)#sort selected bones
        
        name = re.sub(r'\d+','', selected[0].name)
        if(name[-1] == "."):
            name = name[0:-1]

        directions = []
        for bone in selected:
            if(self.axis == "X"):
                directions.append(bone.x_axis)
            elif(self.axis == "-X"):
                directions.append(bone.x_axis * -1)
            elif(self.axis == "Z"):
                directions.append(bone.z_axis)
            elif(self.axis == "-Z"):
                directions.append(bone.z_axis * -1)
            else:
                return {"CANCELLED"}

        points = PointTools.gen_points_from_bones(selected)#gen points from selected
        selected = ArmatureTools.get_bone_names(selected)#get names of selected
        ctrlBones = ArmatureTools.gen_bones_tangent_to_points(objArmature.data.edit_bones, points, directions, 1, name, self.prefix, "")#generate new bones off points

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = objArmature.pose.bones
        for i in range(len(selected)):
            #retrieve pose bone
            bone = poseBones[poseBones.find(selected[i])]
            #Constraint targets
            ctrlH = ctrlBones[i]
            ctrlT = ctrlBones[i+1]
            
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

class Gen_Bone_Chain(bpy.types.Operator):
    bl_idname = "armature.gen_bone_chain"
    bl_label = "bone Chain"
    bl_description = "Creates a chain of stretchy Bones with ctrl bones"

    def __init__(self):
        context = bpy.context
        
        self.objArmature = context.active_object
        self.chainName = "BoneChain"
        self.numBones = 10

    chainName: bpy.props.StringProperty(name="Name of Chain")
    numBones: bpy.props.IntProperty(name="Number of Bones")
    prefix: bpy.props.StringProperty(name="Preffix")
    suffix: bpy.props.StringProperty(name="Suffix")
    parents: bpy.props.BoolProperty(name="Parents?")
    useConnect: bpy.props.BoolProperty(name="UseConnect?")

    @classmethod
    def poll(cls, context):
        if(context.active_object == None): 
            return False

        obj = context.active_object
        isArm = (obj is not None) and (obj.type == "ARMATURE")
        
        return isArm and (((obj.mode == 'EDIT') and (len(context.selected_editable_bones) > 0)) or 
                         ((obj.mode == 'POSE') and (len(context.selected_pose_bones) > 0)))

    def execute(self, context):
        if(self.numBones <= 0 or self.chainName == ""):
            return {'CANCELLED'}

        initMode = self.objArmature.mode
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.objArmature.data.edit_bones
        
        boneSource = bpy.context.selected_editable_bones[0]

        distance = ArmatureTools.bone_to_vectors(boneSource)#returns (loc,dir,dist)
        location = distance[0]
        direction = distance[1]
        distance = distance[2]
        z_axis = boneSource.z_axis

        edit_bones.remove(boneSource)

        points = PointTools.gen_points_along_vector(location, direction, distance, self.numBones + 1)
        defBones = ArmatureTools.gen_bones_along_points(edit_bones, points, self.chainName, self.prefix, self.suffix, parents = self.parents, useConnect = self.useConnect)
        ctrlBones = ArmatureTools.gen_bones_tangent_to_points(edit_bones, points, z_axis, distance/self.numBones, self.chainName, "CTRL_" + self.prefix, self.suffix)

        bpy.ops.object.mode_set(mode='POSE')
        poseBones = self.objArmature.pose.bones
        for i in range(len(defBones)):
            defBone = poseBones[poseBones.find(defBones[i])]
            ctrlH = ctrlBones[i]
            ctrlT = ctrlBones[i+1]

            constraint = defBone.constraints.new('COPY_LOCATION')
            constraint.subtarget = ctrlH
            constraint.target = self.objArmature

            constraint = defBone.constraints.new('STRETCH_TO')
            constraint.subtarget = ctrlT
            constraint.target = self.objArmature

        bpy.ops.object.mode_set(mode=initMode)

        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

#bug. Crash on CTRL Z
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
        self.objArmature = None
        self.objCurve = None

        for i in range(self.numObjs):
            obj = context.selected_objects[i]
            if(obj.type == "CURVE"):
                self.objCurve = obj
            elif(obj.type == "ARMATURE"):
                self.objArmature = obj

    chainName: bpy.props.StringProperty(name="Name of chain")
    preffix: bpy.props.StringProperty(name="Preffix")
    suffix: bpy.props.StringProperty(name="Suffix")
    even: bpy.props.BoolProperty(name="even distribution?")

    @classmethod
    def poll(cls, context):
        numObjs = len(context.selected_objects)
        if(numObjs < 1 or numObjs > 2): return False
        
        curve = False
        armature = False
        
        for i in range(numObjs):
            obj = context.selected_objects[i]
            curve = curve or obj.type == "CURVE"
            armature = armature or obj.type == "ARMATURE"
        
        print(((numObjs == 2) and (curve and armature)) or ((numObjs == 1) and curve))
        return (((numObjs == 2) and (curve and armature)) or ((numObjs == 1) and curve))

    def execute(self, context):
        if(self.numBones == 0):
            return {"CANCELLED"}

        #Acquire armature and set as active object
        if(self.objArmature == None):#create armature if we dont have one
            self.objArmature = bpy.data.objects.new(self.chainName, bpy.data.armatures.new(self.chainName))
            context.scene.collection.objects.link(self.objArmature)
            self.objArmature.select_set(True)
            context.view_layer.objects.active = self.objArmature
        else:#store mode
            self.objArmature.select_set(True)
            context.view_layer.objects.active = self.objArmature

        initMode = self.objArmature.mode

        #get curve information
        spline = self.objCurve.data.splines[0]#each spline is a separate curve in the object
        bPoints = BezierPoint.copyList(spline.bezier_points)#bPoints represent the handles of the curve
        resolution = spline.resolution_u#number of points per segment
        curveSegments = len(bPoints) - 1

        #transformation information from both both objects
        #for i in range(len(bPoints)):#translate bPoints into armature space
        PointTools.bPoints_translate_space(bPoints, self.objCurve, self.objArmature)

        curvePoints = PointTools.gen_points_from_bPoints(bPoints, resolution, evenDistribution = self.even, forBones = True)
        bpy.ops.object.mode_set(mode='EDIT')
        ArmatureTools.gen_bones_along_points(self.objArmature.data.edit_bones, curvePoints, self.name, self.preffix, self.suffix)

        bpy.ops.object.mode_set(mode=initMode)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)