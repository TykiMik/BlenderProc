import warnings

import bpy

from src.renderer.RendererInterface import RendererInterface
from src.utility.Config import Config
from src.utility.MaterialLoaderUtility import MaterialLoaderUtility
from src.utility.RendererUtility import RendererUtility
from src.utility.Utility import Utility


class RgbRenderer(RendererInterface):
    """
    Renders rgb images for each registered keypoint.

    Images are stored as PNG-files or JPEG-files with 8bit color depth.

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - render_texture_less
          - Render all objects with a white slightly glossy texture, does not change emission materials, Default:
            False.
          - bool
        * - image_type
          - Image type of saved rendered images, Default: 'PNG'. Available: ['PNG','JPEG']
          - str
        * - transparent_background
          - Whether to render the background as transparent or not, Default: False.
          - bool
        * - use_motion_blur
          - Use Blender motion blur feature which is required for motion blur and rolling shutter simulation. This
            feature only works if camera poses follow a continous trajectory as Blender performs a Bezier
            interpolation between keyframes and therefore arbitrary results are to be expected if camera poses are
            discontinuous (e.g. when sampled), Default: False
          - bool
        * - motion_blur_length
          - Motion blur effect length (in frames), Default: 0.1
          - float
        * - use_rolling_shutter
          - Use rolling shutter simulation (top to bottom). This depends on the setting enable_motion_blur being
            activated and a motion_blur_length > 0, Default: False
          - bool
        * - rolling_shutter_length
          - Time as fraction of the motion_blur_length one scanline is exposed when enable_rolling_shutter is
            activated. If set to 1, this creates a pure motion blur effect, if set to 0 a pure rolling shutter
            effect, Default: 0.2
          - float
    """
    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less', False)
        self._image_type = config.get_string('image_type', 'PNG')
        self._use_motion_blur = config.get_bool('use_motion_blur', False)
        self._motion_blur_length = config.get_float('motion_blur_length', 0.1)
        self._use_rolling_shutter = config.get_bool('use_rolling_shutter', False)
        self._rolling_shutter_length = config.get_float('rolling_shutter_length', 0.2)


    def run(self):
        # if the rendering is not performed -> it is probably the debug case.
        do_undo = not self._avoid_output
        with Utility.UndoAfterExecution(perform_undo_op=do_undo):
            self._configure_renderer(use_denoiser=self._use_denoiser, default_denoiser="Intel")

            # check if texture less render mode is active
            if self._texture_less_mode:
                MaterialLoaderUtility.change_to_texture_less_render(self._use_alpha_channel)

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=True)

            if self.config.has_param("cf_add_side_blur"):
                cf_config = Config(self.config.get_raw_dict("cf_add_side_blur"))
                self._addSideBlur(cf_config)

            MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)

            # motion blur
            if self._use_motion_blur:
                RendererUtility.enable_motion_blur(self._motion_blur_length, 'TOP' if self._use_rolling_shutter else "NONE", self._rolling_shutter_length)

            self._render(
                "rgb_",
                "colors",
                enable_transparency=self.config.get_bool("transparent_background", False),
                file_format=self._image_type
            )

        if self._image_type == 'PNG':
            self._register_output("rgb_", "colors", ".png", "1.0.0")
        elif self._image_type == 'JPEG':
            self._register_output("rgb_", "colors", ".jpg", "1.0.0")
        else:
            raise Exception("Unknown Image Type " + self._image_type)

    def _addSideBlur(self, config):
        scene = bpy.context.scene
        scene.use_nodes = True
        tree = scene.node_tree
        nodes = tree.nodes
        links = tree.links

        composite_node = nodes.get('Composite')

        render_layer = nodes.get('Render Layers')

        img_blur = nodes.new(type="CompositorNodeBlur")
        img_blur.filter_type = config.get_string("img_blur_type")
        img_blur_kernel_size = config.get_vector2d("img_blur_kernel_size")
        img_blur.size_x = img_blur_kernel_size.x
        img_blur.size_y = img_blur_kernel_size.y

        links.new(render_layer.outputs.get('Image'), img_blur.inputs.get('Image'))

        mask_node = nodes.new(type="CompositorNodeEllipseMask")
        mask_position = config.get_vector2d("ellipse_mask_position")
        mask_node.x = mask_position.x
        mask_node.y = mask_position.y
        mask_node.width = config.get_float("ellipse_mask_width")
        mask_node.height = config.get_float("ellipse_mask_height")

        mask_blur = nodes.new(type="CompositorNodeBlur")
        mask_blur.filter_type = config.get_string("mask_blur_type")
        mask_blur_kernel_size = config.get_vector2d("mask_blur_kernel_size")
        mask_blur.size_x = mask_blur_kernel_size.x
        mask_blur.size_y = mask_blur_kernel_size.y

        links.new(mask_node.outputs.get('Mask'), mask_blur.inputs.get('Image'))

        invert = nodes.new(type="CompositorNodeInvert")

        links.new(mask_blur.outputs.get('Image'), invert.inputs.get('Color'))

        mix_node = nodes.new(type="CompositorNodeMixRGB")

        links.new(invert.outputs.get('Color'), mix_node.inputs[0])
        links.new(render_layer.outputs.get('Image'), mix_node.inputs[1])
        links.new(img_blur.outputs.get('Image'), mix_node.inputs[2])
        links.new(mix_node.outputs.get('Image'), composite_node.inputs.get('Image'))
