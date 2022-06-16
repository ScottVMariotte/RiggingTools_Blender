# BasicRigTools
BasicRigTools is just a collection of rigging operations that are ment to improve the rigging experience in blender. 

## Current Status
Functional - all operations should work as intended with minimal issues.

# Operations

 - **Subdivide Bones -**
	 - requirements - active(ARMATURE), mode(EDIT)
	 - I dont like how blender numbering bones when subdividing. This operation will subdivide selected bones and number them in ascending order from the highest selected bone in the chain. It will also update numbers on any bones down the chain that are not selected. It uses the three-digit (.000) as a base and will rewrite your numbering convention if you use (.00) or (.0). May make it respect numbering conventions later.
	 
 - **Gen Bone Copies -**
	 - requirements - active(ARMATURE), mode(EDIT)
	 - Will duplicate selected bones and add the given prefix. You can make many copies by adding a ',' between each prefix. example = "CTRL_,MECH_").
	 - You can also replace existing string in the name with the new prefix if needed.
	 
 - **Bone Curve -**
	 - requirements - selected(ARMATURE,CURVE), active(ARMATURE), mode(EDIT)
	 - Takes selected curve and turns it into a bone chain. Default distrobution of points is same as 	blender but you can have the bones evenly placed by checking the box.
	 
 - **Snap Bones To Curve-**
 	 - requirements - selected(ARMATURE,CURVE), active(ARMATURE), mode(EDIT)
	 - Snaps selected bones in edit mode to the selected curve. You can have them placed to the closest point on the curve or evenly along the curve.
	 
 - **Gen Bone Chain From Bones-**
 	 - requirements - selected(ARMATURE), active(ARMATURE), mode(EDIT)
	 - Takes selected bones and extrudes control bones. The selected bones are then constrained to the control bones creating a stretchy chain.
	 
 - **Gen Eye Bones-**
 	 - requirements - selected(ARMATURE,MESH), active(MESH), mode(EDIT)
	 - Generates eye bones based on the selected points in the eye mesh. The goal to make this work is to select vertices whose positions will average out to the center of the eye. Lastly, select the center of the pupil and run the operation. Three bones should be created pointing in the direction of the pupil and originating from the center of the eye.
	 
 - **Add Twist Constraints-**
 	- requirements - selected(ARMATURE), active(ARMATURE), mode(POSE)
	- Adds a series of rotation constraints to selected bones to create a twist chain. The actively selected bone acts as the target. You can reverse the direction of the chain by checking the "head?" box.
	
 - **Add Many Constraints-**
 	- requirements - selected(ARMATURE), active(ARMATURE), mode(POSE)
	- Uses the active bone as a target and constrains all other selected bones. You can set the influence in the menue.
	
 - **Toggle Constraints and Remove Constraints-**
 	 - requirements - selected(ARMATURE), active(ARMATURE), mode(POSE)
	 -  Toggle allows you to check whether you want the constraints on selected bones to be on or off. Remove just removes all constraints on selected objects.
	 
- **Merge Parent By Distance-**
 	 - requirements - activeType="ARMATURE", activeMode="EDIT", minBones=1
	 - Connects bones to parents based on distance for selected bones.

