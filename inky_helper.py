from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
import math
from machine import Pin, PWM, Timer
import inky_frame
import os
import gc
import ujson
import time
import network
import uhashlib

"""
inky helper

Utilities and tools to help other modules!

Use:
import inky_helper as ih
"""

# Pin setup for VSYS_HOLD needed to sleep and wake.
HOLD_VSYS_EN_PIN = 2
hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT)

# intialise the pcf85063a real time clock chip
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
rtc = PCF85063A(i2c)

led_warn = Pin(6, Pin.OUT)

# set up for the network LED
network_led_pwm = PWM(Pin(7))
network_led_pwm.freq(1000)
network_led_pwm.duty_u16(0)


# set the brightness of the network led
def network_led(brightness):
    brightness = max(0, min(100, brightness))  # clamp to range
    # gamma correct the brightness (gamma 2.8)
    value = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
    network_led_pwm.duty_u16(value)


network_led_timer = Timer(-1)
network_led_pulse_speed_hz = 1


def network_led_callback(t):
    # updates the network led brightness based on a sinusoid seeded by the current time
    brightness = (math.sin(time.ticks_ms() * math.pi * 2 / (1000 / network_led_pulse_speed_hz)) * 40) + 60
    value = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
    network_led_pwm.duty_u16(value)


# set the network led into pulsing mode
def pulse_network_led(speed_hz=1):
    global network_led_timer, network_led_pulse_speed_hz
    network_led_pulse_speed_hz = speed_hz
    network_led_timer.deinit()
    network_led_timer.init(period=50, mode=Timer.PERIODIC, callback=network_led_callback)


# turn off the network led and disable any pulsing animation that's running
def stop_network_led():
    global network_led_timer
    network_led_timer.deinit()
    network_led_pwm.duty_u16(0)


def sleep(t):
    # Time to have a little nap until the next update
    rtc.clear_timer_flag()
    rtc.set_timer(t, ttp=rtc.TIMER_TICK_1_OVER_60HZ)
    rtc.enable_timer_interrupt(True)

    # Set the HOLD VSYS pin to an input
    # this allows the device to go into sleep mode when on battery power.
    hold_vsys_en_pin.init(Pin.IN)

    # Regular time.sleep for those powering from USB
    time.sleep(60 * t)


def network_connect(SSID, PSK):
    # Enable the Wireless
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Number of attempts to make before timeout
    max_wait = 10

    # Sets the Wireless LED pulsing and attempts to connect to your local network.
    pulse_network_led()
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs
    wlan.connect(SSID, PSK)

    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    stop_network_led()
    network_led_pwm.duty_u16(30000)

    # Handle connection error. Switches the Warn LED on.
    if wlan.status() != 3:
        stop_network_led()
        led_warn.on()

# ----- Turn off button LEDs -----

def clear_button_leds():
    inky_frame.button_a.led_off()
    inky_frame.button_b.led_off()
    inky_frame.button_c.led_off()
    inky_frame.button_d.led_off()
    inky_frame.button_e.led_off()


# ----- Check if file or directory exists -----

def file_exists(filename):
    try:
        return (os.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

def directory_exists(dirname):
    try:
        return (os.stat(dirname)[0] & 0x4000) != 0
    except OSError:
        return False

# ----- Check for duplicate files -----

def get_checksum(filename):
    gc.collect()
    hash = uhashlib.sha256()
    with open(filename, 'rb') as f:
        while chunk := f.read(1024):
            hash.update(chunk)
    gc.collect()
    return hash.digest()

def get_duplicate(directory, filepath):
    file_checksum = get_checksum(filepath)
    for file in os.listdir(directory):
        fp = f'{directory}/{file}'
        if fp != filepath:
            if file_checksum == get_checksum(fp):
                return fp
    return None

def remove_duplicates(directory):
    files_by_hash = dict()
    for file in os.listdir(directory):
        filepath = f'{directory}/{file}'
        checksum = get_checksum(filepath)
        if checksum in files_by_hash:
            remove_file(filepath)
        else:
            files_by_hash[checksum] = filepath

def remove_file(filename):
    try:
        print(f'Delete {filename}')
        os.remove(filename)
    except Exception as e:
        print(f'Error: Failed to delete {filename}. {e}')

# ----- Handle App state -----

state = {'run': 'image_gallery', 'photo_index': 0, 'apod_index': 0, 'xkcd_index': 0, 'clock_index': 0}
app = None

def clear_state():
    if file_exists('state.json'):
        os.remove('state.json')

def save_state(data):
    with open('/state.json', 'w') as f:
        f.write(ujson.dumps(data))
        f.flush()

def load_state():
    global state
    data = ujson.loads(open('/state.json', 'r').read())
    if type(data) is dict:
        state = data

def get_app():
    return state['run']

def get_cycle():
    return state['photo_cycle']

def get_index():
    return state['photo_index']

def get_apod_index():
    return state['apod_index']

def get_xkcd_index():
    return state['xkcd_index']

def get_clock_index():
    return state['clock_index']

def update_app(app):
    global state
    state['run'] = app
    save_state(state)

def update_cycle(cycle):
    global state
    if state['photo_cycle'] != cycle:
        state['photo_cycle'] = cycle
        save_state(state)

def update_index(index):
    global state
    state['photo_index'] = index
    save_state(state)

def update_apod_index(index):
    global state
    state['apod_index'] = index
    save_state(state)

def update_xkcd_index(index):
    global state
    state['apod_index'] = index
    save_state(state)

def update_clock_index(index):
    global state
    state['clock_index'] = index
    save_state(state)

def launch_app(app_name):
    global app
    app = __import__(f'apps/{app_name}')
    update_app(app_name)