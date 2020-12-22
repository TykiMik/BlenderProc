import json
import os
import bpy
import bmesh

from src.utility.Utility import Utility
from src.writer.WriterInterface import WriterInterface


class MetaInformationWriter(WriterInterface):
    """ Writes the state of all objects for each frame to a numpy file if no hfd5 file is available. """

    def __init__(self, config):
        WriterInterface.__init__(self, config)
        self._for_animation = self.config.get_bool("for_animation", False)

    def run(self):
        """ Collect all mesh objects and writes their required attributes to a json file"""
        scene = bpy.context.scene

        objects = self.config.get_list("objects", [])

        if self._for_animation:
            start_seconds = self.config.get_float("animation_start")
            end_seconds = self.config.get_float("animation_end")

            scene.frame_start = self._seconds_to_frames(start_seconds)
            scene.frame_end = self._seconds_to_frames(end_seconds)

        # for each rendered frame
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            cam_obj = scene.camera

            render_width = scene.render.resolution_x * (scene.render.resolution_percentage / 100)
            render_height = scene.render.resolution_y * (scene.render.resolution_percentage / 100)

            scene.frame_set(frame)

            json_array = []

            for obj in objects:
                object_bounds = Utility.camera_view_bounds_2d(scene, cam_obj, obj)
                if self._check_validity(object_bounds, render_width, render_height):
                    attributes_str = self.config.get_string("attributes_to_write", "")
                    attributes = attributes_str.split(", ")

                    object_dict = {}
                    object_dict["name"] = self._get_attribute(obj, "name")
                    for attribute in attributes:
                        if attribute == "cp_volume":
                            attribute_value = self._calculate_volume(obj)
                        else:
                            attribute_value = self._get_attribute(obj, attribute)
                        object_dict[attribute] = attribute_value
                    json_array.append(object_dict)


            target_path = os.path.join(self._determine_output_dir(False), "meta_info_%04d.json" % frame)
            with open(target_path, "w") as outfile:
                json.dump(json_array, outfile)

    def _calculate_volume(self, obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
        bm.transform(obj.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces)

        volume = bm.calc_volume()
        bm.free()

        return volume

    def _check_validity(self, bounds, render_width, render_height):
        x = bounds[0]
        y = bounds[1]
        width = bounds[2]
        height = bounds[3]

        error = 1
        # float comparison with error tolerance
        # left side clamped to zero or right side clamped to render width
        return not (abs(x - 0) <= error or abs((x + width) - render_width) <= error or abs(y - 0) <= error or abs((y + height) - render_height) <= error)

    def _get_attribute(self, object, attribute_name):
        """ Returns the value of the requested attribute for the given object.

        :param object: The mesh object. Type: blender mesh type object.
        :param attribute_name: The attribute name. Type: string.
        :return: The attribute value.
        """
        custom_property = attribute_name.startswith("cp_")
        if hasattr(object, attribute_name) and not custom_property:
            return getattr(object, attribute_name)

        if custom_property:
            custom_property_name = attribute_name[len("cp_"):]
            _attribute_name = "customprop_" + custom_property_name
            return super()._get_attribute(object, _attribute_name)
        else:
            return super()._get_attribute(object, attribute_name)

    def _seconds_to_frames(self, seconds):
        """ Converts the given number of seconds into the corresponding number of blender animation frames.

        :param seconds: The number of seconds. Type: int.
        :return: The number of frames. Type: int.
        """
        return int(seconds * bpy.context.scene.render.fps)
