import warnings

import bpy

from src.renderer.RendererInterface import RendererInterface
from src.utility.Config import Config
from src.utility.Utility import Utility


class RgbRenderer(RendererInterface):
    """ Renders rgb images for each registered keypoint.

    Images are stored as PNG-files or JPEG-files with 8bit color depth.
    .. csv-table::
        :header: "Parameter", "Description"

        "render_texture_less", "Render all objects with a white slightly glossy texture, does not change emission "
                                "materials, Type: bool. Default: False."
        "image_type", "Image type of saved rendered images, Type: str. Default: 'PNG'. Available: ['PNG','JPEG']"
        "transparent_background", "Whether to render the background as transparent or not, Type: bool. Default: False."
        "use_denoiser", "Use the given denoiser on render, Type: bool. Default: True"
    """
    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._texture_less_mode = config.get_bool('render_texture_less', False)
        self._image_type = config.get_string('image_type', 'PNG')
        self._use_denoiser = config.get_bool("use_denoiser", True)

    def change_to_texture_less_render(self):
        """
        Changes the materials, which do not contain a emission shader to a white slightly glossy texture
        :return:
        """
        new_mat = bpy.data.materials.new(name="TextureLess")
        new_mat.use_nodes = True
        nodes = new_mat.node_tree.nodes

        principled_bsdf = Utility.get_the_one_node_with_type(nodes, "BsdfPrincipled")

        # setting the color values for the shader
        principled_bsdf.inputs['Specular'].default_value = 0.65  # specular
        principled_bsdf.inputs['Roughness'].default_value = 0.2  # roughness

        for object in [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]:
            # replace all materials with the new texture less material
            for slot in object.material_slots:
                emission_shader = False
                # check if the material contains an emission shader:
                for node in slot.material.node_tree.nodes:
                    # check if one of the shader nodes is a Emission Shader
                    if 'Emission' in node.bl_idname:
                        emission_shader = True
                        break
                # only replace materials, which do not contain any emission shader
                if not emission_shader:
                    if self._use_alpha_channel:
                        slot.material = self.add_alpha_texture_node(slot.material, new_mat)
                    else:
                        slot.material = new_mat

    def run(self):
        # if the rendering is not performed -> it is probably the debug case.
        do_undo = not self._avoid_rendering
        with Utility.UndoAfterExecution(perform_undo_op=do_undo):
            self._configure_renderer(use_denoiser=self._use_denoiser, default_denoiser="Intel")

            # In case a previous renderer changed these settings
            #Store as RGB by default unless the user specifies store_alpha as true in yaml
            bpy.context.scene.render.image_settings.color_mode = "RGBA" if self.config.get_bool("transparent_background", False) else "RGB"
            #set the background as transparent if transparent_background is true in yaml
            bpy.context.scene.render.film_transparent = self.config.get_bool("transparent_background", False)
            bpy.context.scene.render.image_settings.file_format = self._image_type
            bpy.context.scene.render.image_settings.color_depth = "8"

            # only influences jpg quality
            bpy.context.scene.render.image_settings.quality = 95

            # check if texture less render mode is active
            if self._texture_less_mode:
                self.change_to_texture_less_render()

            if self._use_alpha_channel:
                self.add_alpha_channel_to_textures(blurry_edges=True)

            if self.config.has_param("cf_add_side_blur"):
                cf_config = Config(self.config.get_raw_dict("cf_add_side_blur"))
                self._addSideBlur(cf_config)

            self._render("rgb_")

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

