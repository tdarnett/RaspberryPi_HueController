# Created by Taylor Arnett
# GitHub: tdarnett

############# PACKAGES ###########
from beautifulhue.api import Bridge
import RPi.GPIO as GPIO 	# for button presses
import time
import Adafruit_ADS1x15 	# Import the ADS1x15 module.
##################################

# Setting Up Button GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Using GPIO 18 for button input


###### GLOBAL VARIABLES ###########
# Philips Hue Information
bridge = Bridge(device={'ip':'192.168.0.34'},user = {'name':'PV2PWHlM6fBO-ueKGH5p6CgM2ceihAM9dyKfD3Cj'})
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
lightsToUpdate = [4] # Taylor's room lights are 5 and 6
lastButtonState = False
buttonState = True
lastAnalog = 0
#####################################

# function that updates the hue light through REST request
def updateHue(lights, brightness, saturation, hue):
	# to set maximums that hue lights can read
	if brightness > 254:
		brightness = 254
	if saturation > 254:
		saturation = 254
	if hue > 30000:
		hue = 30000
	
	for light in lights:
		resource = {'which': light,
					'data':{
						'state':{'on':True, 'bri':brightness,'sat':saturation,'hue':hue}
						}
					}
			
		bridge.light.update(resource)
	
	# verbose
	print 'brightness: ' + str(brightness)
	print 'saturation: ' + str(saturation)
	print 'hue: ' + str(hue)

# Function turns off the given light
def turnOff(lights):
	for light in lights:
		resource = {'which': light,
					'data':{
						'state':{'on':False}
						}
					}		
		bridge.light.update(resource)

# Function turns on the given light
def turnOn(lights):
	for light in lights:
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

# This function will adjust the hue of the light using the potentiometer
def adjustHue(lastButtonState, buttonState, lastAnalog):  
	for light in lightsToUpdate:
		initialOn, initialBri, initialSat, initialHue = getState(light)
		#print initialBri
		#print initialSat
		#print initialHue
		updateHue([light],initialBri, initialSat, initialHue)
	#turnOn(lightsToUpdate)
	print 'waiting for input'
	while True:
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
			turnOff(lightsToUpdate)
			print "Turning off lights!"
			time.sleep(2)
			return 			# where we will wait for button press to turn on
	
		lastButtonState = input_state	
	
		# this following block of code will update the lights state only if
		# the potentiometer is incremented or decremented 20mV
		if lastAnalog-analogValue > 20:
			# TODO: MAKE IT SO IT KEEPS THE ORIGIAL SAT AND BRIGHTNESS
			updateHue(lightsToUpdate,getState(lightsToUpdate[0])[1],getState(lightsToUpdate[0])[2],hue)
			print ('updating Hue')
			print ('waiting for input...')
			print ('')
		elif (analogValue-lastAnalog >20):
			updateHue(lightsToUpdate,getState(lightsToUpdate[0])[1],getState(lightsToUpdate[0])[2],hue)
			print ('updating Hue')
			print ('waiting for input...')
			print ('')
			
		lastAnalog = analogValue
		
		time.sleep(0.3)
		
def waitForOn (): 
	print 'waiting for input...' 
	while True:
		button_state = GPIO.input(18)
		if button_state == False:
		    print('Button Pressed')
		    turnOn(lightsToUpdate)
		    adjustHue(lastButtonState, buttonState, lastAnalog)
		      


#MAIN
waitForOn()
adjustHue(lastButtonState, buttonState, lastAnalog)
waitForOn()
		
	

