import numpy as np


import mathutils

from src.main.Provider import Provider


class EqualUniform3d(Provider):
    """ Uniformly samples a 3-dimensional vector.

        Example 1: Return a uniformly sampled 3d vector from a range [min, max] with equal values.

        {
          "provider": "sampler.EqualUniform3d",
          "max": 0.5,
          "min": -0.5
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "min", "A float value, describing the minimum value for the 3d vector's values. Type: float"
        "max", "A float value, describing the maximum value for the 3d vector's values. Type: float"
        "mode", "The way of how to sample values. Type: string. Default: 'uniform'. Available: 'uniform', 'normal'."
        "mean", "Mean (“centre”) of the normal (Gaussian) distribution. Type: float."
        "std_dev", "Standard deviation (spread or “width”) of the normal (Gaussian) distribution. Type: float."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled value. Type: Mathutils Vector
        """

        # sampling mode, default uniform
        mode = self.config.get_string("mode", "uniform")

        if mode == "uniform":
            val_min = self.config.get_float('min')
            val_max = self.config.get_float('max')
            val = np.random.uniform(val_min, val_max)
        elif mode == "normal":
            mean = self.config.get_float('mean')
            std_dev = self.config.get_float('std_dev')
            val = np.random.normal(loc=mean, scale=std_dev)
        else:
            raise Exception("Mode {} doesn't exist".format(mode))

        position = mathutils.Vector()
        for i in range(3):
            position[i] = val

        return position
