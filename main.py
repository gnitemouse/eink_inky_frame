import gc
import os
import time
import sdcard
from machine import Pin, SPI, reset
import inky_frame
import inky_helper as ih
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"

"""
main

Runs automatically upon startup or reboot.
7.3" Inky Frame is powered by PicoW.

Use the Pimoroni Pico Inky Frame libraries and examples found at
https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/examples/inky_frame
Readme.md
https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules_py/inky_frame.md

Picographics library can be found at
https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/modules/picographics

"""

# A short delay to give USB chance to initialise
time.sleep(0.5)

# Status variable to be passed to the app
status = '>>'
status_change = None

# Picographics display setup
graphics = PicoGraphics(DISPLAY)
WIDTH, HEIGHT = graphics.get_bounds()
graphics.set_font("bitmap8")

def setup_sdcard():
    # set up the SD card
    sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16, Pin.OUT))
    sd = sdcard.SDCard(sd_spi, Pin(22))
    if not 'sd' in os.listdir(): # check if SD is mounted
        try:
            os.mount(sd, '/sd')
        except OSError as e:
            print(e)
            graphics.text(e, 0, 40)


def launcher():
    # Inky Frame 7.3"
    y_offset = 35

    # Draws the menu
    graphics.set_pen(1)
    graphics.clear()
    graphics.set_pen(0)

    graphics.set_pen(graphics.create_pen(255, 215, 0))
    graphics.rectangle(0, 0, WIDTH, 50)
    graphics.set_pen(0)
    title = "Launcher"
    title_len = graphics.measure_text(title, 4) // 2
    graphics.text(title, (WIDTH // 2 - title_len), 10, WIDTH, 4)

    graphics.set_pen(4)
    graphics.rectangle(30, HEIGHT - (340 + y_offset), WIDTH - 100, 50)
    graphics.set_pen(1)
    graphics.text("A. << Photo", 35, HEIGHT - (325 + y_offset), 600, 3)

    graphics.set_pen(6)
    graphics.rectangle(30, HEIGHT - (280 + y_offset), WIDTH - 150, 50)
    graphics.set_pen(1)
    graphics.text("B. Photo >>", 35, HEIGHT - (265 + y_offset), 600, 3)

    graphics.set_pen(2)
    graphics.rectangle(30, HEIGHT - (220 + y_offset), WIDTH - 200, 50)
    graphics.set_pen(1)
    graphics.text("C. NASA Picture of the Day", 35, HEIGHT - (205 + y_offset), 600, 3)

    graphics.set_pen(3)
    graphics.rectangle(30, HEIGHT - (160 + y_offset), WIDTH - 250, 50)
    graphics.set_pen(1)
    graphics.text("D. RTC Clock", 35, HEIGHT - (145 + y_offset), 600, 3)

    graphics.set_pen(0)
    graphics.rectangle(30, HEIGHT - (100 + y_offset), WIDTH - 300, 50)
    graphics.set_pen(1)
    graphics.text("E. XKCD Daily", 35, HEIGHT - (85 + y_offset), 600, 3)

    graphics.set_pen(graphics.create_pen(220, 220, 220))
    graphics.rectangle(WIDTH - 100, HEIGHT - (340 + y_offset), 70, 50)
    graphics.rectangle(WIDTH - 150, HEIGHT - (280 + y_offset), 120, 50)
    graphics.rectangle(WIDTH - 200, HEIGHT - (220 + y_offset), 170, 50)
    graphics.rectangle(WIDTH - 250, HEIGHT - (160 + y_offset), 220, 50)
    graphics.rectangle(WIDTH - 300, HEIGHT - (100 + y_offset), 270, 50)

    graphics.set_pen(0)
    note = "Hold A + E, then press Reset, to return to the Launcher"
    note_len = graphics.measure_text(note, 2) // 2
    graphics.text(note, (WIDTH // 2 - note_len), HEIGHT - 30, 600, 2)

    ih.led_warn.on()
    graphics.update()
    ih.led_warn.off()

    # Now we've drawn the menu to the screen, we wait here for the user to select an app.
    # Then once an app is selected, we set that as the current app and reset the device and load into it.
    while True:
        if ih.inky_frame.button_a.read():
            inky_frame.button_a.led_on()
            ih.update_app('image_gallery')
            reset()
        if ih.inky_frame.button_b.read():
            inky_frame.button_b.led_on()
            ih.update_app('image_gallery')
            reset()
        if ih.inky_frame.button_c.read():
            inky_frame.button_c.led_on()
            ih.update_app('nasa_apod')
            reset()
        if ih.inky_frame.button_d.read():
            inky_frame.button_d.led_on()
            ih.update_app('xkcd_daily')
            reset()
        if ih.inky_frame.button_e.read():
            inky_frame.button_e.led_on()
            ih.update_app('rtc_clock')
            reset()


def select_app():
    global status
    global status_change

    if ih.inky_frame.button_a.read():
        inky_frame.button_a.led_on()
        ih.update_app('image_gallery')
        if ih.get_app() == 'image_gallery':
            status = '<<'
            status_change = None
        else:
            status = None
            status_change = '<<'

    elif ih.inky_frame.button_b.read():
        inky_frame.button_b.led_on()
        ih.update_app('image_gallery')
        if ih.get_app() == 'image_gallery':
            status = '>>'
            status_change = None
        else:
            status = None
            status_change = '>>'

    elif ih.inky_frame.button_c.read():
        inky_frame.button_c.led_on()
        ih.update_app('nasa_apod')
        if ih.get_app() == 'nasa_apod':
            status = '>>'
            status_change = None
        else:
            status = None
            status_change = '>>'

    elif ih.inky_frame.button_d.read():
        inky_frame.button_d.led_on()
        ih.update_app('xkcd_daily')
        if ih.get_app() == 'xkcd_daily':
            status = '>>'
            status_change = None
        else:
            status = None
            status_change = '>>'

    elif ih.inky_frame.button_e.read():
        inky_frame.button_e.led_on()
        ih.update_app('rtc_clock')
        if ih.get_app() == 'rtc_clock':
            status = 'wait'
            status_change = None
        else:
            status = 'sync'
            status_change = 'wait'

    elif status_change:
        status = status_change
        status_change = None


def load_app():
    # Launches the app
    ih.load_state()
    ih.launch_app(ih.get_app())

    # Passes the the graphics object from the launcher to the app
    ih.app.graphics = graphics
    ih.app.WIDTH = WIDTH
    ih.app.HEIGHT = HEIGHT
    ih.app.status = status
    
    # Check that SD card is mounted
    if not 'sd' in os.listdir():
        try:
            os.mount(sd, '/sd')
        except OSError as e:
            print(e)
            graphics.text(e, 0, 40)
    gc.collect()

# Display error
def show_error(text):
    graphics.set_pen(4) # red
    graphics.rectangle(0, 10, WIDTH, 35)
    graphics.set_pen(1) # white
    graphics.text(text, 5, 16, 400, 2)

# Display mesesage as caption above
def show_caption(text):
    graphics.set_pen(2) # green
    graphics.rectangle(0, 0, WIDTH, 16)
    graphics.set_pen(1) # white
    graphics.text(text, 2 , 0)

# Turn any LEDs off that may still be on from last run.
ih.clear_button_leds()
ih.led_warn.off()
# SD card setup
setup_sdcard()

if ih.inky_frame.button_a.read() and ih.inky_frame.button_e.read():
    launcher()
elif ih.file_exists("state.json"):
    load_app()
    ih.update_clock_index(0)
else:
    launcher()

try:
    from wifi_config import WIFI_SSID, WIFI_PASSWORD
    ih.network_connect(WIFI_SSID, WIFI_PASSWORD)
except ImportError:
    print("Update wifi_config.py with your WiFi credentials")

# Get some memory back, we really need it!
gc.collect()

# The main loop executes the update and draw function from the imported app,
# and then goes to sleep ZzzzZZz

print('state.json exists:', ih.file_exists("state.json"))

while True:
    if inky_frame.woken_by_rtc() or inky_frame.woken_by_button():
        select_app()
        load_app()
        #print(f'state: {ih.state}')
        #print(f'app: {ih.get_app()}')
        #print(f'status {status} status_change {status_change}')
        ih.app.update()
        ih.led_warn.on()
        ih.app.draw()
        #show_caption(f'{ih.get_app()} status {status}')
        graphics.update()
        ih.led_warn.off()
        ih.clear_button_leds()
        gc.collect()
    inky_frame.sleep_for(ih.app.UPDATE_INTERVAL)