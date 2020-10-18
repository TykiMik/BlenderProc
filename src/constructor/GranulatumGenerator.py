import bpy

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

        if use_file and use_existing and os.path.exists(file_path):
            return

        with Utility.UndoAfterExecution(perform_undo_op=not keep_objects):
            for i in range(amount):
                self._generate_object()

            if use_file:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in bpy.data.objects:
                    if obj.get("generated") is not None:
                        obj.select_set(True)
                bpy.ops.export_scene.obj(filepath=file_path, use_selection=True)


    def _generate_object(self):
        taper_chance = self.config.get_float("taper_chance", 0.5)
        stretch_chance = self.config.get_float("stretch_chance", 0.5)
        max_taper = self.config.get_float("max_taper", 0.5)
        max_stretch = self.config.get_float("max_stretch", 0.5)

        bpy.ops.mesh.primitive_uv_sphere_add()
        sphere = bpy.context.object
        sphere.scale = [0.5, 0.5, 0.5]  # making 1x1x1 sphere instead of the default 2x2x2
        sphere["generated"] = True
        mesh = bpy.context.object.data

        for f in mesh.polygons:
            f.use_smooth = True

        is_tapered = random.random()
        if is_tapered <= taper_chance:
            bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
            taper = bpy.context.object.modifiers['SimpleDeform']
            taper.name = 'taper'
            taper.deform_method = 'TAPER'
            taper.deform_axis = 'Y'
            taper.factor = -random.uniform(0.0, max_taper)
            bpy.ops.object.modifier_apply(modifier='taper')

        is_stretched = random.random()
        if is_stretched <= stretch_chance:
            bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
            taper = bpy.context.object.modifiers['SimpleDeform']
            taper.name = 'stretch'
            taper.deform_method = 'STRETCH'
            taper.deform_axis = 'Y'
            taper.factor = random.uniform(0.0, max_stretch)
            bpy.ops.object.modifier_apply(modifier='stretch')
