import gc
import time
import uasyncio
import inky_frame
import inky_helper as ih
from wifi_config import WIFI_SSID, WIFI_PASSWORD
from network_manager import NetworkManager
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"

"""
RTC clock

Syncs time with network and displays clock.
"""

graphics = None
WIDTH = None
HEIGHT = None
status = None
UPDATE_INTERVAL = 10

# Day of week
DAYOFWEEK = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

# Set tz_offset to be the number of hours off of UTC for your local zone.
# Examples:  tz_offset = -7 # Pacific time (PST)
#            tz_offset =  1 # CEST (Paris)
#            tz_offset =  9 # KST (Seoul)
tz_offset = 9
tz_seconds = tz_offset * 3600
# WLAN country code
# By default, the country setting for the PicoW's wireless network is unset
# Examples: US (United States), KR (South Korea), GB (United Kingdom)
country = 'KR'

# Sync the Inky (always on) RTC to the Pico W so that "time.localtime()" works.
inky_frame.pcf_to_pico_rtc()

def status_handler(mode, status, ip):
    print(mode, status, ip)

def update():

    graphics.set_pen(1)
    graphics.clear()

    # Rainbow background
    for x in range(WIDTH):
        h = x / (1.8*WIDTH)
        p = graphics.create_pen_hsv(h, 1.0, 1.0)
        graphics.set_pen(p)
        graphics.line(x, 0, x, HEIGHT)

    graphics.set_pen(3)
    graphics.rectangle(0, 0, WIDTH, 16)
    graphics.rectangle(0, HEIGHT - 16, WIDTH, 16)
    graphics.set_pen(1)

    year, month, day, hour, minute, second, dow, _ = time.localtime(time.time() + tz_seconds)

    # Connect to the network and set the time
    index = ih.get_clock_index()
    if status == 'sync' or index == 0: # Sync time
        connected = False
        network_manager = NetworkManager('KR', status_handler=status_handler, client_timeout=60)

        t_start = time.time()
        try:
            uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_SSID, WIFI_PASSWORD))
            connected = True
        except RuntimeError:
            pass
        t_end = time.time()

        if connected:
            inky_frame.set_time()

            graphics.text(f'Set time from network... {t_end-t_start}s', 2, HEIGHT-14)
            ih.update_clock_index(index+1)
        else:
            graphics.text('Failed to connect!', 0, HEIGHT-14)

    elif index > 36: # Sync time every 36*UPDATE_INTERVAL mins
        ih.update_clock_index(0) # Reset index


def draw():
    # Display the date and time
    year, month, day, hour, minute, second, dow, _ = time.localtime(time.time() + tz_seconds)

    date = f'{month:02}/{day:02}/{year:04} {DAYOFWEEK[dow]}'
    dtime = f'{hour:02}:{minute:02}'

    graphics.set_font("bitmap8")

    date_scale = 8
    date_height = 8 * date_scale
    time_scale = 24
    time_height = 24 * time_scale

    date_offset_left = (WIDTH - graphics.measure_text(date, scale=date_scale)) // 2
    date_offset_top = (HEIGHT - date_height) // 2 - 2*date_height
    time_offset_left = (WIDTH - graphics.measure_text(dtime, scale=time_scale)) // 2
    time_offset_top = (HEIGHT - date_height) // 2

    graphics.set_pen(3)
    graphics.text(date, date_offset_left + 2, date_offset_top + 2, scale=date_scale)
    graphics.set_pen(7)
    graphics.text(date, date_offset_left, date_offset_top, scale=date_scale)

    graphics.set_pen(3)
    graphics.text(dtime, time_offset_left + 3, time_offset_top + 3, scale=time_scale)
    graphics.set_pen(7)
    graphics.text(dtime, time_offset_left, time_offset_top, scale=time_scale)

    gc.collect()