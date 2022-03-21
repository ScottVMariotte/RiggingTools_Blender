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
            self.handle_right = handle_right
            self.handle_left = handle_left
            self.co = co
    
    @classmethod
    def copyList(cls, bPoints):
        points = []
        for i in range(len(bPoints)):
            points.append(cls(bPoint = bPoints[i]))
        return points

class ArmatureTools:

    @classmethod
    def trim_bone_name(cls, name):
        return re.sub(r'.\d','',name)

    @classmethod
    def gen_bone_name(cls, prifix, name, suffix, num):
        return prifix + name + suffix + "." + str(num).zfill(3)
        #return prifix + name + suffix + zFill 000
        #update blenderOps code to use this function

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
        if(cls.is_contiguous_branchless(bones)):
            top = cls.get_chain_head(bones)
            children = top.children_recursive[:len(bones)-1]
            sortedBones = [top]
            sortedBones.extend(children)
            return sortedBones
        else:
            return bones
    
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

        return count == len(bones) and len(child) <= 1

    @classmethod
    def get_contiguous_sets(cls, bones, sameSize = False, stopBranch = True):
        boneSets = []
        size = None
        bones = bones.copy()
        while(len(bones) > 0):
            #ToDo: remove set from bones and find next set
            bone = cls.get_chain_head(bones)
            set = [bone]
            child = bone.children
            bones.remove(bone)
            while(len(child) == 1 and child[0] in bones):
                bone = child[0]
                bones.remove(bone)
                set.append(bone)
                child = bone.children
            if(size == None):#gets size of first set
                size = len(set)
            
            halt = (sameSize and (len(set) != size)) or (stopBranch and len(child) > 1)
            
            if(halt):
                return []
            
            boneSets.append(set)
                
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
    def gen_bones_tangent_to_points(cls, editBones, points, direction, size, name, prefix, suffix):
        isList = type(direction) == list
        startDir = direction.copy()
        length = len(points)
        bones = []

        if(isList):
            direction = startDir[0]
        length = len(points)
        for i in range(length):
            newName = prefix + name + suffix + "." + str(i).zfill(3)
            bones.append(newName)

            if(isList and i != 0):
                if(i < length - 1):
                    direction = startDir[i].copy()
                    direction += startDir[i-1]
                    direction = direction.normalized()
                else:
                    direction = startDir[len(startDir)-1]
   

            bone = editBones.new(newName)
            bone.head = points[i]
            bone.tail = bone.head + (direction * size)

        if(isList):
            direction = startDir[0]

        return bones

    @classmethod
    def gen_bones_along_points(cls, editBones, points, names, prefix, suffix, parents = True, useConnect = True, rolls = 0):
        bones = []

        name = ""
        boneLast = None
        for i in range(len(points) - 1):
            newName = prefix + names[i] + suffix if (type(names) == list) else prefix + names + suffix 
            roll = rolls[i] if (type(rolls) == list) else rolls

            newName = newName if (type(names) == list) else newName + "." + str(i).zfill(3)
            bones.append(newName)
            bone = editBones.new(newName)
            bone.head = points[i]
            bone.tail = points[i + 1]
            bone.roll = roll

            if(i > 0 and parents and boneLast != None):
                bone.parent = boneLast
                bone.use_connect = useConnect

            boneLast = bone

        return bones

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
        Length = LUT[n - 1]
        
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
    def __distance_of_LUTS(cls, LUTS):
        distance = 0
        numBezSegments = len(LUTS)
        LUTResolution = len(LUTS[0])
        for i in range(numBezSegments):
            distance += LUTS[i][LUTResolution-1]
        return distance

    @classmethod
    def gen_points_from_bones(cls, bones, offset = 1):
        points = []
        points.append(bones[0].head)

        numPoints = int(len(bones) / offset)
        for i in range(1,numPoints+1):
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
    def points_translate_space(cls, points, local, other):
        mat = SimpleMaths.get_space_transform_mat(local, other)
        for point in points:
            point = mat @ point

        return points

    @classmethod
    def bezier_points_translate_space(cls, bPoints, local, other):
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
            points = cls.bezier_points_to_curve(bPoints, LUTResolution)
            #calculating cumulative distance from point to point along each curve segment
            for i in range(numBezSegments):
                LUT = [0.0]              #cumulative distnace values get put here
                for j in range(LUTResolution):
                    index = (i * (LUTResolution)) + j
                    distance = math.dist(points[index],points[index + 1]) + LUT[j]
                    LUT.append(distance)
                LUTS.append(LUT)

            #values for next part of curve gen
            points = []
            curveLength = cls.__distance_of_LUTS(LUTS)

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

                points.append(cls.__T_to_point(knot1, handle1, handle2, knot2, cls.__distance_to_T(LUTS[LUTIndex], distance)))

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

