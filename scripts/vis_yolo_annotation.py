import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--image', dest='image', default='examples/granulatum/output/rgb_000.png' ,help='image over which to annotate', type=str)
parser.add_argument('-a', '--annotation', dest='annotation', default='examples/granulatum/output/rgb_000.txt', help='path to yolo annotation txt', type=str)

args = parser.parse_args()

image_path = args.image
annotation_path = args.annotation
img_array= np.array(Image.open(image_path), dtype=np.uint8)

height, width, channels = img_array.shape


# Create figure and axes
fig,ax = plt.subplots(1)

objects = open(annotation_path)
lines = objects.readlines()
objects.close()

for line in lines:
    line = line[0:-2]
    box = tuple(map(float, line.split(' ')))
    box = box[1:]

    print(width)
    print(height)
    box_width = (box[2] * width)
    box_height = (box[3] * height)
    left_x = (box[0] * width - box_width/2)
    left_y = (box[1] * height - box_height/2)

    # Create a Rectangle patch
    rect = patches.Rectangle((left_x, left_y), box_width, box_height, linewidth=1, edgecolor='r', facecolor='none')
    # Add the patch to the Axes
    ax.add_patch(rect)

# Display the image
ax.imshow(img_array)

plt.show()