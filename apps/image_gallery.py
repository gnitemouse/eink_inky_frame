import jpegdec
import os
import gc
import inky_frame
import inky_helper as ih
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"

"""
image gallery

An offline image gallery that displays jpg images from an SD card.
Copy images to the /photos directory of your SD card by plugging it into a computer.
Images must be 800x480px or smaller and saved as *non-progressive* jpgs.

"""

graphics = None
WIDTH = None
HEIGHT = None
status = None
# Length of time between updates in minutes.
# Frequent updates will reduce battery life!
UPDATE_INTERVAL = 15
# Image location
IMGDIR = '/sd/photos'

# Image files
images = None
# Image/photo index
index = None

def decrement_index(index):
    if index == 0:
        index = len(images)-1
    else:
        index -= 1
    return index

def increment_index(index):
    if index == len(images)-1:
        index = 0
    else:
        index += 1
    return index

def update_index(index):
    global status
    if status:
        if status == '>>':
            return increment_index(index)
        elif status == '<<':
            return decrement_index(index)
        else:
            print(f'Error: Cycle status {status} is invalid. Assuming >>')
            status = '>>'
            return increment_index(index)
    return index
    
def is_jpg(filename):
    if '.jpg' in filename or '.jpeg' in filename:
        return True
    elif '.JPG' in filename or '.JPEG' in filename:
        return True
    else:
        return False

def display_image(jdecoder, filename):
    # Open the JPEG file
    jdecoder.open_file(f'{IMGDIR}/{filename}')

    # Decode the JPEG
    jdecoder.decode(0, 0, jpegdec.JPEG_SCALE_FULL)
    gc.collect()

def update():
    global images
    global index
    
    images = os.listdir(IMGDIR)
    
    index = ih.get_index()
    index = update_index(index)
    while not is_jpg(images[index]):
        index = update_index(index)
    ih.update_index(index)
    print('Current photo index:', index)


def draw():
    # Create a new JPEG decoder for our PicoGraphics
    j = jpegdec.JPEG(graphics)
    gc.collect()

    print(f'Displaying {images[index]}')
    display_image(j, images[index])