import time
import settings
from beautifulhue.api import Bridge
import RPi.GPIO as GPIO  # for button presses
import adafruit_ads1x15.ads1015 as ADS # Import the ADS1x15 module.


# Setting Up Button GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Using GPIO 18 for button input

BRIDGE = Bridge(device={'ip': '192.168.0.34'}, user={'name': settings.HUE_API_KEY}) # Philips Hue Information
# create an ADS1015 ADC (12-bit) instance.
# Choose a gain of 1 for reading voltages from 0 to 4.09V.
# Or pick a different gain to change the range of voltages that are read:
#  - 2/3 = +/-6.144V
#  -   1 = +/-4.096V
#  -   2 = +/-2.048V
#  -   4 = +/-1.024V
#  -   8 = +/-0.512V
#  -  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
ADC = ADS.ADS1015()
GAIN = 1

ON_TOGGLE = True
LIGHTS_TO_UPDATE = [settings.ROOM_LIGHT]  # Room lights are 5 and 6
LAST_BUTTON_STATE = False
BUTTON_STATE = True
LAST_HUE_ANALOG = 0
LAST_BRI_ANALOG = 0

# function that updates the hue light through REST request
def update_hue(lights, brightness, saturation, hue):
    # to set maximums that hue lights can read
    # if brightness > 254:
    # brightness = 254
    if saturation > 254:
        saturation = 254
    if hue > 30000:
        hue = 30000

    for light in lights:
        resource = {
            'which': light,
            'data': {
                'state': {'on': True, 'bri': brightness, 'sat': saturation, 'hue': hue}
            }
        }

        BRIDGE.light.update(resource)

    # verbose
    print('brightness: %s' % brightness)
    print('saturation: %s' % saturation)
    print('hue: %s' % hue)


# Function turns off the given light
def turn_off(lights):
    for light in lights:
        resource = {'which': light,
                    'data': {
                        'state': {'on': False}
                    }
                    }
        BRIDGE.light.update(resource)


# Function turns on the given light
def turn_on(lights):
    for light in lights:
        resource = {'which': light,
                    'data': {
                        'state': {'on': True}
                    }
                    }

        BRIDGE.light.update(resource)


# returns the light's current state, brightness, saturation and hue
def get_state(light):
    resource = {'which': light}
    result = BRIDGE.light.get(resource)
    # print result
    data = result['resource']
    state = data['state']

    # each information
    is_on = state[''u'on']  # True or False
    get_bri = state[''u'bri']
    get_sat = state[''u'sat']
    get_hue = state[''u'hue']

    return is_on, get_bri, get_sat, get_hue


# This will map the values from the potentiometer to the range of the hue
def translate(value, left_min, left_max, right_min, right_max):
    # Figure out how 'wide' each range is
    left_span = left_max - left_min
    right_span = right_max - right_min

    # Convert the left range into a 0-1 range (float)
    value_scaled = float(value - left_min) / float(left_span)

    # Convert the 0-1 range into a value in the right range.
    return int(right_min + (value_scaled * right_span))


def adjust_lights(last_button_state, button_state, last_bri_analog, last_hue_analog):
    for light in LIGHTS_TO_UPDATE:
        initial_on, initial_bri, initial_sat, initial_hue = get_state(light)
        update_hue([light], initial_bri, initial_sat, initial_hue)
    print('waiting for input')
    while True:
        input_state = GPIO.input(18)

        # Read the specified ADC channel using the previously set gain value.
        analog_hue_value = ADC.read_adc(0, gain=GAIN)
        analog_bri_value = ADC.read_adc(3, gain=GAIN)

        hue = translate(analog_hue_value, 0, 1648, 0, 30000)
        bri = translate(analog_bri_value, 0, 1648, 0, 254)

        if input_state and not last_button_state:
            button_state = not button_state
        if not button_state:
            turn_off(LIGHTS_TO_UPDATE)
            print("Turning off lights!")
            time.sleep(2)
            return  # where we will wait for button press to turn on

        last_button_state = input_state

        # this following block of code will update the lights state only if
        # the potentiometer is incremented or decremented 20mV
        if last_hue_analog - analog_hue_value > 20:
            # TODO: MAKE IT SO IT KEEPS THE ORIGINAL SAT AND BRIGHTNESS
            print('BRIGHTNESS IS %s' % get_state(LIGHTS_TO_UPDATE[0])[1])
            update_hue(LIGHTS_TO_UPDATE, get_state(LIGHTS_TO_UPDATE[0])[1], get_state(LIGHTS_TO_UPDATE[0])[2], hue)
        elif analog_hue_value - last_hue_analog > 20:
            update_hue(LIGHTS_TO_UPDATE, get_state(LIGHTS_TO_UPDATE[0])[1], get_state(LIGHTS_TO_UPDATE[0])[2], hue)

        print('updating Hue')
        print('waiting for input...\n')
        last_hue_analog = analog_hue_value
        time.sleep(0.3)

        # this following block of code will update the lights brightness only if
        # the potentiometer is incremented or decremented 20mV
        if last_bri_analog - analog_bri_value > 20:
            # TODO: MAKE IT SO IT KEEPS THE ORIGINAL SAT AND BRIGHTNESS
            update_hue(LIGHTS_TO_UPDATE, bri, get_state(LIGHTS_TO_UPDATE[0])[2], get_state(LIGHTS_TO_UPDATE[0])[3])

        elif (analog_bri_value - last_bri_analog > 20):
            update_hue(LIGHTS_TO_UPDATE, bri, get_state(LIGHTS_TO_UPDATE[0])[2], get_state(LIGHTS_TO_UPDATE[0])[3])
        print('updating Brightness')
        print('waiting for input...\n')
        last_bri_analog = analog_bri_value

        time.sleep(0.3)


def wait_for_on():
    if get_state(LIGHTS_TO_UPDATE[0])[0]:
        adjust_lights(LAST_BUTTON_STATE, BUTTON_STATE, LAST_BRI_ANALOG, LAST_HUE_ANALOG)
    print('waiting for input...')
    while True:
        button_state = GPIO.input(18)
        if not button_state:
            print('Button Pressed')
            turn_on(LIGHTS_TO_UPDATE)
            adjust_lights(LAST_BUTTON_STATE, button_state, LAST_BRI_ANALOG, LAST_HUE_ANALOG)


# MAIN
wait_for_on()
adjust_lights(LAST_BUTTON_STATE, BUTTON_STATE, LAST_BRI_ANALOG, LAST_HUE_ANALOG)
wait_for_on()
