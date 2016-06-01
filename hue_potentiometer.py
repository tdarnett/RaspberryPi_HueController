
# Created by Taylor Arnett
# GitHub: tdarnett

# TOD0: make it so the brightness doesnt change when the hue potentiometer doesnt move

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
lastHueAnalog = 0
lastBriAnalog = 0
#####################################

# function that updates the hue light through REST request
def updateHue(lights, brightness, saturation, hue):
	# to set maximums that hue lights can read
	#if brightness > 254:
		#brightness = 254
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

def adjustLights(lastButtonState, buttonState, lastBriAnalog, lastHueAnalog):
	for light in lightsToUpdate:
		initialOn, initialBri, initialSat, initialHue = getState(light)
		updateHue([light],initialBri, initialSat, initialHue)
	print 'waiting for input'
	while True:
		input_state = GPIO.input(18)
		hue = 0
		bri = 0
		
		# Read the specified ADC channel using the previously set gain value.
		analogHueValue = adc.read_adc(0, gain=GAIN)
		analogBriValue = adc.read_adc(3, gain=GAIN)
		
		hue = translate(analogHueValue, 0, 1648,0,30000)
		bri = translate(analogBriValue, 0, 1648,0,254)
	
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
		if lastHueAnalog-analogHueValue > 20:
			# TODO: MAKE IT SO IT KEEPS THE ORIGIAL SAT AND BRIGHTNESS
			print 'BRIGHTNESS IS ', str(getState(lightsToUpdate[0])[1])
			updateHue(lightsToUpdate,getState(lightsToUpdate[0])[1],getState(lightsToUpdate[0])[2],hue)
			print ('updating Hue')
			print ('waiting for input...')
			print ('')
		elif (analogHueValue-lastHueAnalog >20):
			updateHue(lightsToUpdate,getState(lightsToUpdate[0])[1],getState(lightsToUpdate[0])[2],hue)
			print ('updating Hue')
			print ('waiting for input...')
			print ('')	
		lastHueAnalog = analogHueValue
		time.sleep(0.3)
		
		# this following block of code will update the lights brightness only if
		# the potentiometer is incremented or decremented 20mV
		if lastBriAnalog-analogBriValue > 20:
			# TODO: MAKE IT SO IT KEEPS THE ORIGIAL SAT AND BRIGHTNESS
			updateHue(lightsToUpdate,bri,getState(lightsToUpdate[0])[2],getState(lightsToUpdate[0])[3])
			print ('updating Brightness')
			print ('waiting for input...')
			print ('')
		elif (analogBriValue-lastBriAnalog >20):
			updateHue(lightsToUpdate,bri,getState(lightsToUpdate[0])[2],getState(lightsToUpdate[0])[3])
			print ('updating Brightness')
			print ('waiting for input...')
			print ('')	
		lastBriAnalog = analogBriValue
		
		time.sleep(0.3)
	
def waitForOn (): 
	if (getState(lightsToUpdate[0])[0]):
		adjustLights(lastButtonState, buttonState, lastBriAnalog, lastHueAnalog)
	print 'waiting for input...' 
	while True:
		button_state = GPIO.input(18)
		if button_state == False:
		    print('Button Pressed')
		    turnOn(lightsToUpdate)
		    adjustLights(lastButtonState, buttonState, lastBriAnalog, lastHueAnalog)
		      


#MAIN
waitForOn()
adjustLights(lastButtonState, buttonState, lastBriAnalog, lastHueAnalog)
waitForOn()
		
	

