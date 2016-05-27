# TOD0:
#	- test with the group of lights in Taylor's Room (lights 6 & 7)
#	- make the button press response more crisp
#	- clean up code

############# PACKAGES ###########
from beautifulhue.api import Bridge
import RPi.GPIO as GPIO 	# for button presses
import time
from random import randint
import Adafruit_ADS1x15 	# Import the ADS1x15 module.
##################################

# Setting Up Button GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)


###### GLOBAL VARIABLES ###########
# Philips Hue Information
bridge = Bridge(device={'ip':'192.168.0.40'},user = {'name':'PV2PWHlM6fBO-ueKGH5p6CgM2ceihAM9dyKfD3Cj'})
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
adc = Adafruit_ADS1x15.ADS1015()
GAIN = 1

onToggle = True
which = 4
lastButtonState = False
buttonState = True
#####################################


def update(which, onToggle, brightness, saturation, hue):
	if brightness > 254:
		brightness = 254
	
	if saturation > 254:
		saturation = 254
	if hue > 30000:
		hue = 30000
	
	resource = {'which': which,
				'data':{
					'state':{'on':onToggle, 'bri':brightness,'sat':saturation,'hue':hue}
					}
				}
			
	bridge.light.update(resource)
	print 'brightness: ' + str(brightness)
	print 'saturation: ' + str(saturation)
	print 'hue: ' + str(hue)

def turnOff(light):
	resource = {'which': light,
				'data':{
					'state':{'on':False}
					}
				}
			
	bridge.light.update(resource)

def turnOn(light):
	resource = {'which': light,
				'data':{
					'state':{'on':True}
					}
				}
			
	bridge.light.update(resource)
	
#returns the light's current state, brightness, saturation and hue
def getState(light):
	resource = {'which':light}
	result = bridge.light.get(resource)
	#print result
	data = result['resource']
	state = data['state']
	
	#each information
	isOn = state[''u'on'] # True or False
	getBri = state[''u'bri']
	getSat = state[''u'sat']
	getHue = state [''u'hue']

	return isOn, getBri, getSat, getHue
	
# This will map the values from the potentiometer to the range of the hue
def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return int(rightMin + (valueScaled * rightSpan))

def adjustHue(lastButtonState, buttonState):  
	turnOn(which)
	while True:
		#lastBrightness = getState(which)[1]
		#lastSaturation = getState(which)[2]
		lastHue = getState(which)[3]
		input_state = GPIO.input(18)
		hue = 0
	
		# Read the specified ADC channel using the previously set gain value.
		analogValue = adc.read_adc(0, gain=GAIN)
		hue = translate(analogValue, 0, 1648,0,30000)
	
		if (input_state == True & lastButtonState == False):
			if (buttonState == True):
				buttonState = False
			else:
				buttonState = True
	
		if buttonState == False:
			turnOff(4)
			print "Turning off lights!"
			time.sleep(0.2)
			return #where we will wait fo button press to turn on
	
		lastButtonState = input_state
	
		if (lastHue >= hue):
			if (lastHue-hue > 20):
				update(which,onToggle,255,255,hue)
				print ('updating Hue')
		else:
			if (hue-lastHue >20):
				update(which,onToggle,255,255,hue)
				print ('updating Hue')
			
		time.sleep(0.3)
		
def waitForOn ():  
	while True:
		button_state = GPIO.input(18)
		if button_state == False:
		    print('Button Pressed')
		    turnOn(which)
		    adjustHue(lastButtonState, buttonState)
		      


#MAIN
adjustHue(lastButtonState, buttonState)
waitForOn()
		
	

