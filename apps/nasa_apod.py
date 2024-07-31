import os
import gc
import time
import jpegdec
import ujson
from urllib import urequest
from ucollections import OrderedDict
import inky_helper as ih

graphics = None
WIDTH = None
HEIGHT = None
status = None
# Length of time between updates in minutes.
# Frequent updates will reduce battery life!
UPDATE_INTERVAL = 240

FILENAME = 'nasa-apod'
# Image location
FILEDIR = '/sd/nasa_apod'
# Log file to store NASA APOD dates and titles
FILELOG = 'nasa-apod-log.json'
# Maximum number of files to keep
MAXFILES = 10

# A Demo Key is used in this example and is IP rate limited. You can get your own API Key from https://api.nasa.gov/
API_URL = 'https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY'
IMG_URL = 'https://pimoroni.github.io/feed2image/nasa-apod-800x480-daily.jpg'

# Store NASA APOD titles {filename:title}
apod_log = list()
# Image index
index = None

def clear_log():
    if file_exists(FILELOG):
        ih.remove_file(FILELOG)

def save_log(apod_log):
    with open(FILELOG, 'w') as f:
        f.write(ujson.dumps(dict(apod_log)))
        f.flush()

def load_log():
    global apod_log
    if not ih.file_exists(FILELOG):
        print(f'Creating log {FILELOG}')
        data = open(FILELOG, 'w')
        data.close()
    else:
        print(f'Loading log {FILELOG}')
        data = ujson.loads(open(FILELOG, 'r').read())
        if type(data) is dict:
            # Make sorted list
            apod_log = sorted(data.items())
            print('NASA APOD Log:')
            for file, title in apod_log:
                print(f'{file}: {title}')

def find_title_in_apod_log(name):
    for file, title in apod_log:
        if name == title:
            return file
    return None

def update_index(index):
    if index == len(apod_log)-1:
        index = 0
    else:
        index += 1
    return index

def get_current_index(filename):
    index = 0
    for file, title in apod_log:
        if file == filename:
            return index
        index += 0
    return -1

def update():
    global apod_log
    global index

    # Get index
    index = ih.get_apod_index()

    # Check that image directory exists
    if not ih.directory_exists(FILEDIR):
        os.mkdir(FILEDIR)
    # Get today's date
    year, month, day, hour, minute, second, dow, _ = time.localtime()
    date = f'{month:02}.{day:02}.{year:04}'

    if not apod_log:
        load_log()
    # Check for valid index
    if type(index) is not int:
        print(f'Error: NASA APOD index {index} is invalid. Assume 0.')
        index = 0
    elif index > len(apod_log) - 1:
        index = len(apod_log) - 1

    if os.listdir(FILEDIR): # Downloaded files exist
        if not apod_log: # No logged files
            for file in sorted(os.listdir(FILEDIR)):
                apod_log.append((file, file))
            index = len(apod_log)-1
        # Delete extra files
        if len(apod_log) > MAXFILES:
            for file, title in apod_log[:len(apod_log)-MAXFILES]:
                ih.remove_file(file)
                apod_log.pop(0)
            index = len(apod_log)-1
    else:
        index = 0

    filename = f'{FILENAME}_{date}.jpg'
    if ih.file_exists(f'{FILEDIR}/{filename}'):
        # Image is already downloaded
        findindex = get_current_index(filename)
        if findindex > -1: # File found in log
            if status: # Cycle to next image
                index = update_index(index)
            else:
                index = findindex
        else: # Log doesn't contain file
            print(f'Warning: Image exists but not found in {FILELOG}')
            apod_log.append((filename, '{date} Image Title Unavailable'))
            index = len(apod_log)-1

    else: # Download image if not downloaded already
        title = None
        try:
            # Grab the data
            socket = urequest.urlopen(API_URL)
            gc.collect()
            j = ujson.load(socket)
            socket.close()
            title = j['title']
            gc.collect()
        except OSError as e:
            print(e)
            title = '{date} Image Title Unavailable'

        # Check if image has duplicate in log
        dupe = find_title_in_apod_log(title)
        if dupe:
            print(f'Found duplicate: {dupe} {title}')
            if status: # Cycle to next image
                index = update_index(index)
            else:
                index = len(apod_log)-1
        else:
            try:
                # Grab the image
                socket = urequest.urlopen(IMG_URL)
                gc.collect()

                data = bytearray(1024)
                with open(f'{FILEDIR}/{filename}', "wb") as f:
                    while True:
                        if socket.readinto(data) == 0:
                            break
                        f.write(data)
                socket.close()
                del data
                gc.collect()
                apod_log.append((filename, title))
                index = len(apod_log)-1

            except OSError as e:
                print(e)
                ih.show_error(f'Unable to download image "{title}"')

    save_log(apod_log)
    print(f'Update: {apod_log}')
    ih.update_apod_index(index)

def draw():
    jpeg = jpegdec.JPEG(graphics)
    gc.collect()

    graphics.set_pen(1)
    graphics.clear()

    try:
        print(f'Current apod index: {index}')
        print(f'Displaying {apod_log[index][0]}')
        jpeg.open_file(f'{FILEDIR}/{apod_log[index][0]}')
        jpeg.decode()
    except OSError:
        if not ih.file_exists(file):
            apod_log.pop(file)
            save_log(apod_log)
        graphics.set_pen(4)
        graphics.rectangle(0, (HEIGHT // 2) - 20, WIDTH, 40)
        graphics.set_pen(1)
        graphics.text("Unable to display image!", 5, (HEIGHT // 2) - 15, WIDTH, 2)
        graphics.text("Check your network settings or SD card.", 5, (HEIGHT // 2) + 2, WIDTH, 2)

    graphics.set_pen(0)
    graphics.rectangle(0, HEIGHT - 25, WIDTH, 25)
    graphics.set_pen(1)
    graphics.text(apod_log[index][1], 5, HEIGHT - 20, WIDTH, 2)

    gc.collect()