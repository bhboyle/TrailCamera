
# required libraries
import configparser
import time
import os
from datetime import datetime
from gpiozero import LED, Button
import logging

# **********  setup section  ***************
os.system('echo 0  | sudo tee /sys/class/leds/led0/brightness')


# open the config file
#config = configparser.ConfigParser()
config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
config.read('/home/bboyle/camera.ini')

# set the input pin for the PIR sensor and set it for active high
button = Button(15, pull_up=False) 

# define the output pin for the Infrared LEDS 
led = LED(14)

#  Read the config file and store the values in variables
currentCount = config.get('main', 'imageCount')
interval = config.get('main', 'interval')
minimumImageGap = config.get('main', 'minimumImageGap')
fileNamePrefix = config.get('main', 'fileNamePrefix')
foldrify = config.get('main', 'foldrify')
captionText = config.get('main', 'captionText')
FudSize = config.get('main', 'FudSize')
IncludeOverlay = config.get('main', 'IncludeOverlay')
indicatorLed = config.get('main', 'indicatorLed')
logFile=config.get('main', 'logFile')
loggingStatus=config.get('main', 'loggingStatus')

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p' ,filename=logFile, encoding='utf-8', level=logging.INFO)


# get the current time at startup so the interval checking will work.
oldpoch = time.time()

if loggingStatus == "True":
	logging.info('Startup completed.')

# **********  forever loop  ***************
while True: 


	# add a short sleep to give the CPU time to do other things and not run at 100%
	time.sleep(.05) 

	# if the trigger from the motion sensor is active then check to see how long it has been since the last picture was taken
	if button.is_pressed:

		if loggingStatus == "True":
			logging.info('Trigger recived')

		# check to see if minimumImageGap has passed since the last picture. if so then take another one
		if time.time() - oldpoch >= float(minimumImageGap):
			
			if loggingStatus == "True":
				logging.info('Trigger susessful')

			# turn on the IR LEDs before taking a picture
			led.on()

			# if the IndicatorLed variable is true then turn on the onbaord LED
			if indicatorLed =="True":
				os.system('echo 1  | sudo tee /sys/class/leds/led0/brightness')

			if loggingStatus == "True":
				logging.info('Image taken')

			# take the actual picture
			os.system('libcamera-jpeg --tuning-file /usr/share/libcamera/ipa/raspberrypi/imx708_noir.json -t 5 -o /home/bboyle/pictures/output.jpg')

			# Turn off the IR LEDs once the images is captured
			led.off()

			if loggingStatus == "True":
				logging.info('Overlay added')

			# turn off the onboard indicator LED if needed
			if indicatorLed =="True":
				os.system('echo 0  | sudo tee /sys/class/leds/led0/brightness')

			# if IncludeOverlay is true then Elmer Fudd will be added to teh bottom left corner of the image
			if IncludeOverlay == "True":
				os.system('composite -gravity SouthWest \( /home/bboyle/pictures/Elmer_Fudd.png -resize ' + FudSize + '% \) /home/bboyle/pictures/output.jpg /home/bboyle/pictures/last.jpg')
			
			else :
				os.system('cp output.jpg last.jpg')

			# let the picture get saved
			#time.sleep(.5)

			# current date and time
			now = datetime.now() 

			# create a string that holds the text of the current date and time for the caption at the botton of the picture
			dateString = now.strftime("%A %b %-d %Y, %H:%M:%S") 

			# check the folderify config setting and create the directory variable based on the setting
			if foldrify == "True" :
				# create the string date for use in the folder
				todayDate = time.strftime("%b-%-d-%Y")

				# create the string that is used for the folder
				directory = '/var/www/html/photos/' + todayDate
			else :
				directory = '/var/www/html/photos/'

			if loggingStatus == "True":
				logging.info('Folder confirmed')

			# check if the date folder exists and if not create it.
			if not os.path.exists(directory):
				os.makedirs(directory)

			# increment the image count
			currentCount = str(int(currentCount) + 1)

			# add the current picture number to the caption text
			leftCaption = captionText + " #" + currentCount

			# add the captions at the bottom of the picture and move the file into the gallery
			os.system('convert /home/bboyle/pictures/last.jpg  -pointsize 90 -fill black  -gravity Southwest -background white -splice 0x125 -annotate +30+03 "' + leftCaption + '" -gravity SouthEast  -annotate +30+03 "' + dateString + '" -append '+ directory + '/' + fileNamePrefix + currentCount + '.jpg ')

			if loggingStatus == "True":
				logging.info('Caption added to image #%s', currentCount)

			# Set the image currentCount variable to the setting in the config file
			config.set('main', 'imageCount', currentCount)

			# resave the current image counter back into the config file
			with open('/home/bboyle/camera.ini', 'w') as configfile:
				config.write(configfile)

			if loggingStatus == "True":
				logging.info('Image counter updated')

			# capture the time of the last image so we can make sure it does not take a picture before the minmum interval
			oldpoch = time.time()	
