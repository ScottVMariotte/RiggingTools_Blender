# BasicRigTools
BasicRigTools is just a collection of rigging operations that are ment to improve the rigging experience in blender. 

## Current Status
Functional - all operations should work as intended with minimal issues.\
Looking into writing a testing script for existing operations so I can quickly identify if any new changes have caused issues.

# Operations

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
	- Adds a series of rotation constraints to selected bones to create a twist chain. The actively selected bone acts as the target. You can reverse the direction of the chain by checking the "head? "box.
 - **Add Many Constraints-**
 	- requirements - selected(ARMATURE), active(ARMATURE), mode(POSE)
	- Uses the active bone as a target and constrains all other selected bones. You can set the influence in the menue.
 - **Toggle Constraints and Remove Constraints-**
 	 - requirements - selected(ARMATURE), active(ARMATURE), mode(POSE)
	 -  Toggle allows you to check whether you want the constraints on selected bones to be on or off. Remove just removes all constraints on selected objects.



# Bone Curve 
--(Plan on getting a video up at some points I know the pictures kinda suck...)--
![2022-03-24 18_06_44-Blender](https://user-images.githubusercontent.com/102049585/160018603-8811c026-623a-4441-8407-378873b69c29.png)
# Constrain Bones
![2022-03-24 18_08_01-Blender](https://user-images.githubusercontent.com/102049585/160018622-53cc836a-bbe2-407c-ae88-c6871f1d7a9a.png)

![2022-03-24 18_08_26-Blender](https://user-images.githubusercontent.com/102049585/160018627-44891af4-8b74-4f29-8932-f86e239803c0.png)
# Twist Bones
![2022-03-24 18_09_15-Blender](https://user-images.githubusercontent.com/102049585/160018628-c4bea9e2-39c5-4055-9e77-16ec67d0f469.png)

![2022-03-24 18_09_43-Blender](https://user-images.githubusercontent.com/102049585/160018631-80703e6e-ce99-4521-9c75-4bf00feccf57.png)

![2022-03-24 18_10_00-Blender](https://user-images.githubusercontent.com/102049585/160018636-7896bac2-f5ec-46bb-9bb5-61bc9567cf12.png)

![2022-03-24 18_10_19-Blender](https://user-images.githubusercontent.com/102049585/160018637-1db5f158-4856-463a-a7f7-e5a8da9b2fa8.png)
