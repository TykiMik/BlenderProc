import bpy
from mathutils import Vector
import numpy as np

class VisibilityUtility:

    @staticmethod
    def _get_visible_objects():
        context = bpy.context
        scene = bpy.data.scenes['Scene']
        camera = bpy.context.scene.camera

        # Getting the camera frame corners in the camera local coordinate system
        frame = camera.data.view_frame(scene=bpy.context.scene)
        topRight = frame[0]
        bottomRight = frame[2]
        bottomLeft = frame[2]
        topLeft = frame[3]

        # Calculating the resolution of the frame, dividing by 10 for speedup, we will check for every 10th pixel
        resolutionX = int((
            bpy.context.scene.render.resolution_x * (bpy.context.scene.render.resolution_percentage / 100)) / 10)
        resolutionY = int((
            bpy.context.scene.render.resolution_y * (bpy.context.scene.render.resolution_percentage / 100)) / 10)

        # setup vectors to match pixels
        xRange = np.linspace(topLeft[0], topRight[0], resolutionX)
        yRange = np.linspace(topLeft[1], bottomLeft[1], resolutionY)

        # Going trough the pixel values and casting a ray for detecting visible objects
        visible_objects = []
        for x in xRange:
            for y in yRange:
                # The z coordinate in the camera local space is the depth, it is the same for all the frame coordinates.
                pixelVector = Vector((x, y, topLeft[2]))
                # Transforming the coordinate from camera local space to the global coordinate system.
                globalVector = camera.matrix_world @ pixelVector

                # The direction where the ray should be fired from the camera
                direction = (globalVector - camera.location).normalized()

                # Dependency graph for the evaluated object data
                depsgraph = context.evaluated_depsgraph_get()
                success, _, _, _, intersected_object, _ = scene.ray_cast(depsgraph, camera.location, direction)
                if success:
                    visible_objects.append(intersected_object)

        return set(visible_objects)

    @staticmethod
    def only_visible_objects(objects_to_check):
        if len(objects_to_check) == 0:
            return []

        visible_objects = VisibilityUtility._get_visible_objects()

        filtered_objects = [obj for obj in objects_to_check if obj in visible_objects]
        return filtered_objects
