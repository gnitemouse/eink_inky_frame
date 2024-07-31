import gc
import os
import time
import jpegdec
import uasyncio
from wifi_config import WIFI_SSID, WIFI_PASSWORD
from urllib import urequest
from network_manager import NetworkManager
import inky_helper as ih

"""
xkcd daily

You *must* insert an SD card into Inky Frame!
We need somewhere to save the jpg for display.

Fetches a pre-processed XKCD daily image from:
https://pimoroni.github.io/feed2image/xkcd-daily.jpg

See https://xkcd.com/ for more webcomics!
"""

graphics = None
WIDTH = None
HEIGHT = None
status = None
UPDATE_INTERVAL = 240

FILENAME = 'xkcd-daily'
FILEDIR = '/sd/xkcd'
FILELOG = 'xkcd-log.json'
MAXFILES = 10

ENDPOINT = 'https://pimoroni.github.io/feed2image/xkcd-800x480-daily.jpg'

# xkcd comic to display
comic = None

def update_index(comics, index):
    if index == len(comics)-1:
        index = 0
    else:
        index += 1
    return index

def status_handler(mode, status, ip):
    print(mode, status, ip)

def update():
    global comic

    # Make sure that image directory exists
    if not ih.directory_exists(FILEDIR):
        os.mkdir(FILEDIR)
    # Get date
    year, month, day, hour, minute, second, dow, _ = time.localtime()
    date = f'{month:02}.{day:02}.{year:04}'
    filename = f'{FILENAME}_{date}.jpg'
    filepath = f'{FILEDIR}/{filename}'

    # Get index
    index = ih.get_xkcd_index()
    if type(index) is not int:
        print(f'Error: XKCD index {index} is invalid. Assume 0.')
        index = 0
    # Get files
    comics = sorted(os.listdir(FILEDIR))
    print(f'XKCD Log: {comics}')

    # Delete extra files
    if len(comics) > MAXFILES:
        for file in comics[:len(comics)-MAXFILES]:
            ih.remove_file(file)

    if not ih.file_exists(filepath):
        # Download today's xkcd comic
        network_manager = NetworkManager("KR", status_handler=status_handler)
        uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_SSID, WIFI_PASSWORD))
        url = ENDPOINT

        socket = urequest.urlopen(url)
        gc.collect() # We're really gonna need that RAM!

        # Stream the image data from the socket onto disk in 1024 byte chunks
        # the 600x448-ish jpeg will be roughly ~24k, we really don't have the RAM!
        data = bytearray(1024)
        with open(filepath, "wb") as f:
            while True:
                if socket.readinto(data) == 0:
                    break
                f.write(data)
        socket.close()
        gc.collect()  # We really are tight on RAM!

        # Check if downloaded comic has duplicate
        dupe = ih.get_duplicate(FILEDIR, filepath)
        if dupe:
            print(f'Found duplicate: {dupe}')
            ih.remove_file(dupe)

    comics = sorted(os.listdir(FILEDIR))
    print(f'Update: {comics}')
    # Update index
    if status: # Cycle to next image
        index = update_index(comics, index)
    else:
        index = len(comics)-1
    ih.update_xkcd_index(index)
    # Choose comic to display
    comic = comics[index]

def draw():
    jpeg = jpegdec.JPEG(graphics)
    gc.collect()  # For good measure...

    graphics.set_pen(1)
    graphics.clear()

    try:
        print(f'Displaying {comic}')
        jpeg.open_file(f'{FILEDIR}/{comic}')
        jpeg.decode()
    except OSError:
        graphics.set_pen(4)
        graphics.rectangle(0, (HEIGHT // 2) - 20, WIDTH, 40)
        graphics.set_pen(1)
        graphics.text("Unable to display image!", 5, (HEIGHT // 2) - 15, WIDTH, 2)
        graphics.text("Check your network settings or SD card.", 5, (HEIGHT // 2) + 2, WIDTH, 2)

    gc.collect()