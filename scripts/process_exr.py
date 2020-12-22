import os
import cv2
import sys
import glob


def create_jpg(base_dir, exrfile):
    # load the image
    print("{}:".format(exrfile))
    image = cv2.imread(exrfile,  cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # BGR -> RGB
    jpgfile = str(os.path.basename(exrfile)).split('.')[0] + '.jpg'
    print("{}:".format(jpgfile))
    cv2.imwrite('%s%s' % (base_dir,jpgfile), img)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: process_exr.py <exrfile>")
    base_dir = sys.argv[1] + '/'
    for image_file in glob.iglob('%s*.exr' % base_dir):
        create_jpg(base_dir,image_file)