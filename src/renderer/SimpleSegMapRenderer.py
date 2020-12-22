import csv
import os
import random

import bpy
import mathutils
import numpy as np

from src.renderer.RendererInterface import RendererInterface
from src.utility.BlenderUtility import load_image, get_all_mesh_objects
from src.utility.Utility import Utility


class SimpleSegMapRenderer(RendererInterface):

    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._for_animation = self.config.get_bool("for_animation", False)
        self._image_type = self.config.get_string("image_type", "PNG")

    def _colorize_object(self, obj, color):
        # Create new material emitting the given color
        new_mat = bpy.data.materials.new(name="segmentation")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links
        emission_node = nodes.new(type='ShaderNodeEmission')
        output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')

        emission_node.inputs['Color'].default_value = color
        links.new(emission_node.outputs['Emission'], output.inputs['Surface'])

        # Set material to be used for coloring all faces of the given object
        if len(obj.material_slots) > 0:
            for i in range(len(obj.material_slots)):
                if self._use_alpha_channel:
                    obj.data.materials[i] = self.add_alpha_texture_node(obj.material_slots[i].material, new_mat)
                else:
                    obj.data.materials[i] = new_mat
        else:
            obj.data.materials.append(new_mat)

    def _generate_color(self):
        """ Samples a RGBA vector uniformly for each component.

        :return: RGBA vector. Type: mathutils.Vector
        """
        # minimum values vector
        min = mathutils.Vector([0, 0, 0, 0])
        # maximum values vector
        max = mathutils.Vector([1, 1, 1, 1])

        color = mathutils.Vector([0, 0, 0, 0])
        for i in range(4):
            if 0 <= min[i] <= 1 and 0 <= max[i] <= 1:
                    color[i] = random.uniform(min[i], max[i])

        return color

    def _colorize_objects_for_instance_segmentation(self, objects):
        """ Sets a different color to each object.

        :param objects: A list of objects.
        """

        colors = []
        for idx, obj in enumerate(objects):
            color = self._generate_color()
            while (color in colors):
                color = self._generate_color()

            self._colorize_object(obj, color)


    def _set_world_background_color(self, color):
        """ Set the background color of the blender world obejct.

        :param color: A 4-dim array containing the background color
        """
        nodes = bpy.context.scene.world.node_tree.nodes
        nodes.get("Background").inputs['Color'].default_value = color

    def run(self):
        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)

            # Get objects with meshes (i.e. not lights or cameras)
            objs_with_mats = get_all_mesh_objects()

            backgorund_color = mathutils.Vector([1, 1, 1, 0])
            self._set_world_background_color(backgorund_color)

            self._colorize_objects_for_instance_segmentation(objs_with_mats)

            bpy.context.scene.render.image_settings.file_format = self._image_type
            bpy.context.scene.render.image_settings.color_depth = "16"
            bpy.context.view_layer.cycles.use_denoising = False
            bpy.context.scene.cycles.filter_width = 0.0

            if self._for_animation:
                bpy.context.scene.render.fps = self.config.get_int("animation_fps", 24)
                start_seconds = self.config.get_float("animation_start")
                end_seconds = self.config.get_float("animation_end")

                bpy.context.scene.frame_start = self._seconds_to_frames(start_seconds)
                bpy.context.scene.frame_end = self._seconds_to_frames(end_seconds)

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=False)

            # Determine path for temporary and for final output
            temporary_segmentation_file_path = os.path.join(self._temp_dir, "seg_")

            # Render the temporary output
            self._render("seg_", custom_file_path=temporary_segmentation_file_path)

    def _seconds_to_frames(self, seconds):
        """ Converts the given number of seconds into the corresponding number of blender animation frames.

        :param seconds: The number of seconds. Type: int.
        :return: The number of frames. Type: int.
        """
        return int(seconds * bpy.context.scene.render.fps)