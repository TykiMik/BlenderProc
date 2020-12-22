import bpy

import math
import random
import os

from src.main.Module import Module
from src.utility.Utility import Utility

class GranulatumGenerator(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        output_path = self.config.get_string("output_path", "")
        amount = self.config.get_int("amount", 100)
        use_existing = self.config.get_bool("use_existing", True)

        file_path = Utility.resolve_path(output_path)
        use_file = self.config.get_bool("use_file", True)
        keep_objects = self.config.get_bool("keep_objects", False)
        keep_loose_parts = self.config.get_bool("keep_loose_parts", False)

        if use_file and use_existing and os.path.exists(file_path):
            return

        with Utility.UndoAfterExecution(perform_undo_op=not keep_objects):
            for i in range(amount):
                self._generate_object()

            if use_file:
                bpy.ops.object.select_all(action='DESELECT')
                already_selected = 0
                for obj in bpy.data.objects:
                    if obj.get("generated") is not None:
                        if already_selected < amount:
                            obj.select_set(True)
                            already_selected += 1
                        else:
                            if keep_loose_parts:
                                obj.select_set(True)
                                already_selected += 1
                            else:
                                break
                bpy.ops.export_scene.obj(filepath=file_path, use_selection=True)


    def _generate_object(self):
        # Creating the metaball data, instantiating it and attaching it to the active scene.
        mball = bpy.data.metaballs.new('MetaBall')
        obj = bpy.data.objects.new('MetaBallObj', mball)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

        # Setting the resolution of the ball (think of it as how fine you want it to be)

        mball.render_resolution = self.config.get_float("render_resolution", 0.03)
        obj.data.threshold = self.config.get_float("threshold", 0.4)

        min_element_count = self.config.get_int("min_element", 1)
        max_element_count = self.config.get_int("max_element", 20)
        meta_element_count = random.randint(min_element_count, max_element_count)
        for i in range(meta_element_count):
            coordinate = self._sphere_coordinate(meta_element_count / 5)
            element = mball.elements.new()
            element.co = coordinate

            min_radius = self.config.get_float("min_radius", 1.0)
            max_radius = self.config.get_float("max_radius", 2.0)
            element.radius = random.uniform(min_radius, max_radius)

        # convert metaballs to mesh with bmesh module
        depsgraph = bpy.context.evaluated_depsgraph_get()
        meta_eval = obj.evaluated_get(depsgraph)

        tmpMesh = bpy.data.meshes.new_from_object(meta_eval)
        tmpMesh.transform(obj.matrix_world)

        final_obj = bpy.data.objects.new('Granulatum_obj', tmpMesh)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(final_obj)

        final_obj["generated"] = True

        bpy.ops.object.select_all(action='DESELECT')
        final_obj.select_set(True)
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.select_all(action='DESELECT')

        # Delete metaball object
        bpy.data.objects.remove(obj)
        bpy.data.metaballs.remove(mball)


    def _cube_root(self, num):
        return num ** (1. / 3)

    def _sphere_coordinate(self, radius):
        phi = random.uniform(0, 2 * math.pi)
        costheta = random.uniform(-1, 1)
        u = random.uniform(0, 1)

        theta = math.acos(costheta)
        r = radius * self._cube_root(u)

        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.sin(phi)
        z = r * math.cos(theta)
        return (x, y, z)
