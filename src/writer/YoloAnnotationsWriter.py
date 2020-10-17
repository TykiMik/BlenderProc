import os
import bpy

from src.writer.WriterInterface import WriterInterface
from src.utility.Utility import Utility


class YoloAnnotationsWriter(WriterInterface):
    """ Writes Yolo Annotations in to a file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       
       "avoid_rendering", "If true, no output is produced. Type: bool. Default: False"
       "rgb_output_key", "The output key with which the rgb images were registered. Should be the same as the "
                         "output_key of the RgbRenderer module. Type: string.Default: colors."
       "objs_to_annotate", "List of objects that will be annotated. Result of the getter.Entity. Type: list. Default: []"
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)

        self._avoid_rendering = config.get_bool("avoid_rendering", False)
        self.rgb_output_key = self.config.get_string("rgb_output_key", "colors")

    def run(self):
        """ Writes yolo annotations in the following steps:
        1. Locate the rgb maps
        2. For each frame write the Yolo annotation
        """
        if self._avoid_rendering:
            print("Avoid rendering is on, no output produced!")
            return

        # Find path pattern of rgb images
        rgb_output = self._find_registered_output_by_key(self.rgb_output_key)
        if rgb_output is None:
            raise Exception("There is no output registered with key {}. Are you sure you ran the RgbRenderer module "
                            "before?".format(self.rgb_output_key))

        scene = bpy.context.scene

        # for each rendered frame
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            target_path = os.path.join(self._determine_output_dir(False), rgb_output["path"] % frame).replace(".png", ".txt")

            cam_obj = scene.camera

            render_width = scene.render.resolution_x * (scene.render.resolution_percentage / 100)
            render_height = scene.render.resolution_y * (scene.render.resolution_percentage / 100)

            scene.frame_set(frame)

            file = open(target_path, "w")
            count = 1
            for obj in self.config.get_list("objs_to_annotate", []):
                if obj.get("classId") is None:
                    raise Exception("There is no classId custom property registered to the object: {}. "
                                    "You have to assign the property to every object you want to annotate".format(obj.name))

                object_bounds = Utility.camera_view_bounds_2d(scene, cam_obj, obj)
                if all(object_bounds):
                    rel_center_x = (object_bounds[0]+object_bounds[2]/2) / render_width
                    rel_center_y = (object_bounds[1]-object_bounds[3]/2) / render_height
                    rel_width = object_bounds[2] / render_width
                    rel_height = object_bounds[3] / render_height
                    yolo_format = f"{rel_center_x} {rel_center_y} {rel_width} {rel_height}"
                    file.write(f'{obj["classId"]} {yolo_format} \n')
                    count += 1

        scene.frame_set(scene.frame_start)
