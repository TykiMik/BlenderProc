import random

import mathutils

from src.main.Provider import Provider


class Uniform2d(Provider):
    """ Uniformly samples a 2-dimensional vector.

        Example 1: Return a uniform;y sampled 2d vector from a range [min, max].

        {
          "provider": "sampler.Uniform2d",
          "max": [0.5, 0.5],
          "min": [-0.5, -0.5]
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "min", "A list of three values, describing the minimum values of 1st and 2nd dimensions. Type: list."
        "max", "A list of three values, describing the maximum values of 1st, and 2nd dimensions. Type: list."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled value. Type: Mathutils Vector
        """
        # minimum values vector
        min = self.config.get_vector2d("min")
        # maximum values vector
        max = self.config.get_vector2d("max")

        x_value = random.uniform(min[0], max[0])
        y_value = random.uniform(min[1], max[1])
        position = mathutils.Vector((x_value,y_value))

        return position
