import bpy
import mathutils
import math
import re

#TODO Finish gen Bone name / Parse bone name

class SimpleMaths:
    
    @classmethod
    def find_factors(cls,num):
        nums = []
        for i in range(1,num+1):
            if(num % i == 0):
                nums.append(i)
        return nums

    @classmethod
    def get_space_transform_mat(cls, local, other):
        otherLoc = other.location
        otherRot = other.rotation_euler.to_matrix()
        localLoc = local.location
        LocalRot = local.rotation_euler.to_matrix()

        LocalRot.resize_4x4()
        otherRot.resize_4x4()
        otherRot.transpose()

        return( otherRot @
                mathutils.Matrix.Translation(otherLoc * -1) @
                mathutils.Matrix.Translation(localLoc) @
                LocalRot
                )
        
class BezierPoint:
    def __init__(self, handle_right = None, handle_left = None, co = None, bPoint = None):
        pass
        if(bPoint is not None):
            self.handle_right = bPoint.handle_right.copy()
            self.handle_left = bPoint.handle_left.copy()
            self.co = bPoint.co.copy()
        else:
            self.handle_right = handle_right.copy()
            self.handle_left = handle_left.copy()
            self.co = co.copy()
    
    @classmethod
    def copyList(cls, bPoints):
        points = []
        for i in range(len(bPoints)):
            points.append(cls(bPoint = bPoints[i]))
        return points

class Poll:

    @classmethod
    def selected_types(cls, types):
        for t in types:
            for obj in bpy.context.selectable_objects:
                if(obj.type == t):
                    objs.append(obj)
                    break
        
        return objs
    
    @classmethod
    def num_objects(cls):
        return len(bpy.context.selected_editable_objects)

    @classmethod
    def is_types_selected(cls, types):
        if(types == ""):
            return True
        
        count = 0
        types = types.split(',')
        for t in types:
            for obj in bpy.context.selected_editable_objects:
                if(obj.type == t):
                    count += 1
                    break

        return len(types) == count

    @classmethod
    def is_type_active(cls, t):
        return bpy.context.active_object.type == t or t == ""

    @classmethod
    def is_active_mode(cls, mode):
        return bpy.context.active_object.mode == mode or mode == ""

    @classmethod
    def is_active_none(cls):
        return bpy.context.active_object == None

    @classmethod
    def check_poll(cls, types = "", activeType = "", activeMode = "", numObjs = -1):
        return (
                not cls.is_active_none() and
                (cls.num_objects() == numObjs or numObjs == -1) and
                cls.is_types_selected(types) and 
                cls.is_type_active(activeType) and 
                cls.is_active_mode(activeMode)
                )

class Naming:

    @classmethod
    def compare_names(cls, name1, name2, trim1 = False, trim2 = False):
        if(trim1):
            name1 = Naming.split(name1)
            name1 = name1[0] + name1[2]
        if(trim2):
            name2 = Naming.split(name2)
            name2 = name2[0] + name2[2]
        return name1 == name2

    @classmethod
    def split(cls, name):
        split = name.split(".")

        nums = ""
        name = ""
        mirror = ""
        for s in split:
            if(s == "L" or s == "R"):
                mirror = "." + s
                continue
            if(re.search('[a-zA-Z]', s)):
                name += s + "."
                continue
            if(nums == ""):
                nums = s

        return (name[0:-1], nums, mirror)

    @classmethod
    def gen_new(cls, name, count = -1, prefix = "", suffix = "", mirror = ""):
        if mirror != "":
            mirror = "." + mirror
        if count != -1:
            count = "." + str(count).zfill(3)
        else:
            count = ""
        
        return prefix + name + suffix + count + mirror
    
    @classmethod
    def rename(cls, name):
        name = cls.split(name)
        if name[1] != "":
            return name[0] + "." + str(int(name[1])).zfill(3) + name[2]
        
        return name[0] + name[1] + name[2]

class ArmatureTools:

    @classmethod
    def trim_bone_name(cls, name):
        return re.sub(r'.\d','',name)

    @classmethod
    def gen_bone_name(cls, prefix, name, suffix, num = 0):
        subNames = name.split()
        newName = prefix
        for i in range(len(subNames) - 1):
            newName += subNames[i] + "."

        if(num > 0):#if we have a number to add to the end
            if(re.search('[a-zA-Z]', subNames[-1])):#if the last subName has characters we want to include it
                newName += subNames[-1] + suffix + "." + str(num).zfill(3)
            else:
                newName += suffix + "." + str(num).zfill(3)
        else:
            newName += suffix + "." + subNames[-1]

        return newName

    @classmethod
    def gen_new_names(cls, prefix, names, suffix, extend = 0):
        newNames = []
        for name in names:
            subNames = name.split()
            newName = prefix
            for i in range(len(subNames) - 1):
                newName += subNames[i] + "."

            if(not subNames[-1].isdigit()):
                newName += subNames[-1] + suffix
            else:
                 newName += suffix + "." + subNames[-1]

            newNames.append(newName)
        
        #gens extend more names by using the last new name as template
        if(extend != 0):
            base = ""
            last = newNames[-1]
            subNames = last.split(".")
            offset = int(subNames[-1]) + 1 if(subNames[-1].isdigit()) else 1
            for i in range(len(subNames) - 1):
                base += subNames[i] + "."

            for i in range(extend):
                newNames.append(base + str(i + offset).zfill(3))

        return newNames

    @classmethod
    def get_chain_head(cls, bones):
        head = bones[0]
        parent = head.parent
        while(parent in bones):
            head = parent
            parent = head.parent
        
        return head

    @classmethod
    def get_sorted(cls, bones):
        if(not cls.is_contiguous_branchless(bones)):
            raise "Error in " + __name__ + " : bone chain is not contiguous and branchless!"
            return bones

        top = cls.get_chain_head(bones)
        children = top.children_recursive[:len(bones)-1]
        sortedBones = [top]
        sortedBones.extend(children)
        return sortedBones
  
    @classmethod
    def get_bone_names(cls, bones):
        names = []
        for bone in bones:
            names.append(bone.name)
        return names

    @classmethod
    def is_contiguous_branchless(cls, bones):
        head = cls.get_chain_head(bones)
        
        count = 1
        tail = head
        child = tail.children
        while(len(child) == 1 and child[0] in bones):
            count += 1
            tail = child[0]
            child = tail.children

        return count == len(bones)

    @classmethod
    def get_contiguous_sets(cls, bones):
        boneSets = []
        bones = bones.copy()
        while(len(bones) > 0):
            bone = cls.get_chain_head(bones)
            children = bone.children_recursive
            subSet = [bone]

            bones.remove(bone)
            for i in range(len(children)):
                child = children[i]
                if(child in bones):
                    subSet.append(child)
                    bones.remove(child)
            boneSets.append(subSet)

        return boneSets

    @classmethod
    def bone_to_vectors(cls, bone):
        length = math.dist(bone.tail, bone.head)
        direction = (bone.tail - bone.head)/length
        location = bone.head
        return (location, direction, length)

    @classmethod
    def snap_bones_to_points(cls, bones, points):
        length = len(bones)
        for i in range(length):
            bones[i].head = points[i]
            bones[i].tail = points[i+1]

    @classmethod
    def gen_bones_along_points(cls, editBones, points, names, parents = True, useConnect = True, offset = 1, rolls = 0, z_axis = -1):
        bones = []

        boneLast = None
        for i in range(0,len(points) - 1, offset):
            newName = names[int(i/offset)]
            roll = rolls[i] if (type(rolls) == list) else rolls
            
            bones.append(newName)
            bone = editBones.new(newName)
            bone.head = points[i]
            bone.tail = points[i + 1]
            bone.roll = roll

            z = z_axis if type(z_axis) != list else z_axis[i]
            if(z != -1):
                bone.z_axis = z

            if(i > 0 and parents and boneLast != None):
                bone.parent = boneLast
                bone.use_connect = useConnect

            boneLast = bone

class PointTools:
    
    @classmethod
    def __T_to_point(cls, p0, p1, p2, p3, t):
        t2 = math.pow(t,2)
        t3 = math.pow(t,3)
        return  (((-1 * p0 * t3) + (3 * p0 * t2) - (3 * p0 * t) + p0) + 
                ((3 * p1 * t3) - (6 * p1 * t2) + (3 * p1 * t)) + 
                ((-3 * p2 * t3) + 3 * p2 * t2) + 
                (p3 * t3))

    @classmethod
    def __distance_to_T(cls, LUT, distance):
        n = len(LUT)
        
        for i in range(n-1):
            prevDist = LUT[i]
            nextDist = LUT[i+1]
            if(prevDist <= distance < nextDist):
                prevT = i / (n - 1.0)
                nextT = (i + 1.0) / (n - 1.0)
                t = (distance - prevDist) / (nextDist - prevDist)
                t = ((1.0 - t) * prevT) + (t * nextT)
                return t
        return 1.0

    @classmethod
    def __distance_to_Lut_Index(cls, LUTS, dist):
        numLUTS = len(LUTS)
        resolution = len(LUTS[0])-1
        cumulative = 0.0
        for i in range(numLUTS):
            cumulative += LUTS[i][resolution]
            if(dist <= cumulative):
                return i
        return numLUTS-1

    @classmethod
    def gen_points_from_bones(cls, bones, offset = 1):
        points = []
        points.append(bones[0].head)
        numPoints = int(len(bones) / offset) + 1
        for i in range(1,numPoints):
            index = int((i * offset)) - 1
            points.append(bones[index].tail)

        return points

    @classmethod
    def gen_points_along_vector(cls, loc, dir, distance, numPoints):
        points = []
        delta = distance / (numPoints-1)
        for i in range(numPoints):
            points.append((i * delta * dir) + loc)

        return points
    
    @classmethod
    def gen_points_tangent_to_points(cls, points, directions, distance, includeOriginal = False, avrageDirections = False):
        newPoints = []
        numPoints = len(points)
        dirSingle = type(directions) != list
        if(dirSingle and len(points) > directions):
            raise "Error in " + __name__ + " : number of direction vectors is less than number of points!"
            return points
        
        for i in range(numPoints):
            if(dirSingle):
                direction = directions
            elif(avrageDirections):
                direction = directions[i].copy()
                direction += directions[i-1] * (i > 0)
                direction = direction.normalized()
            else:
                direction = directions[i]

            if(includeOriginal):
                newPoints.append(points[i] * mathutils.Vector((1,1,1)))

            newPoints.append(points[i] + (direction * distance))
        
        return newPoints

    @classmethod
    def points_translate_space(cls, points, local, other):
        mat = SimpleMaths.get_space_transform_mat(local, other)
        for point in points:
            point = mat @ point

        return points

    @classmethod
    def bPoints_translate_space(cls, bPoints, local, other):
        mat = SimpleMaths.get_space_transform_mat(local, other)
        for bp in bPoints:
            bp.handle_right = mat @ bp.handle_right
            bp.handle_left = mat @ bp.handle_left
            bp.co = mat @ bp.co
    
    @classmethod
    def gen_points_from_bPoints(cls, bPoints, resolution, evenDistribution = False, forBones = False):
        points = []
        numBezSegments = len(bPoints) - 1
        if(evenDistribution):        
            LUTResolution = resolution
            LUTS = []

            curveLength = 0
            points = cls.gen_points_from_bPoints(bPoints, LUTResolution)
            #calculating cumulative distance from point to point along each curve segment
            for i in range(numBezSegments):
                LUT = [0.0]              #cumulative distnace values get put here
                for j in range(LUTResolution):
                    index = (i * (LUTResolution)) + j
                    distance = math.dist(points[index],points[index + 1]) + LUT[j]
                    LUT.append(distance)
                LUTS.append(LUT)
                curveLength += LUT[-1]
            points = []
            
            delta = curveLength / (resolution * numBezSegments)
            resolution = (resolution * numBezSegments) + numBezSegments

            #bezier handle info 
            knot1 = bPoints[0].co
            handle1 = bPoints[0].handle_right
            knot2 = bPoints[1].co
            handle2 = bPoints[1].handle_left
            
            LUTIndex = 0    #current distance table index
            LUTdistance = 0 #stores the cumulative distance of the LUT tables as we go

            points.append(cls.__T_to_point(knot1, handle1, handle2, knot2, 0.0))
            for i in range(1,resolution):
                distance = i * delta

                newLUTIndex = cls.__distance_to_Lut_Index(LUTS, distance)#get the relevant distnace table index
                if(newLUTIndex != LUTIndex):#if we pass into a new distance table we need to update cumulative distance
                    LUTdistance += LUTS[LUTIndex][LUTResolution-1]
                    LUTIndex = newLUTIndex
                
                    knot1 = bPoints[LUTIndex].co
                    handle1 = bPoints[LUTIndex].handle_right
                    knot2 = bPoints[LUTIndex+1].co
                    handle2 = bPoints[LUTIndex+1].handle_left

                distance -= LUTdistance

                t = 1.0
                #search through LUT and find t value
                for i in range(LUTResolution-1):
                    prevDist = LUT[i]
                    nextDist = LUT[i+1]
                    if(prevDist <= distance < nextDist):
                        prevT = i / (LUTResolution - 1.0)
                        nextT = (i + 1.0) / (LUTResolution - 1.0)
                        t = (distance - prevDist) / (nextDist - prevDist)
                        t = ((1.0 - t) * prevT) + (t * nextT)

                points.append(cls.__T_to_point(knot1, handle1, handle2, knot2, t))

        else:
            
            b1 = bPoints[0]
            b2 = bPoints[1]

            #get handles from bez point
            knot1 = b1.co
            handle1 = b1.handle_right
            knot2 = b2.co
            handle2 = b2.handle_left
            
            for i in range(numBezSegments):
                b1 = bPoints[i]
                b2 = bPoints[i+1]

                #get handles from bez point
                knot1 = b1.co
                handle1 = b1.handle_right
                knot2 = b2.co
                handle2 = b2.handle_left

                points.append(cls.__T_to_point(knot1, handle1, handle2, knot2, 0.0))
                #calculating points on curve segments
                for i in range(1,resolution):
                    t = i/(resolution)  
                    points.append(cls.__T_to_point(knot1, handle1, handle2, knot2, t))

            points.append(cls.__T_to_point(knot1, handle1, handle2, knot2, 1.0))

        return points

    @classmethod
    def get_length_points(cls, points):
        distance = 0.0
        for i in range(len(points) - 1):
            distance += math.dist(points[i], points[i+1])
        return distance
