import sys
import time
import serial
# test a process with following steps:
# 1. initialize the button

port_number = 0
connected = False
while not connected and port_number < 4:
    port = "/dev/ttyACM%d" % port_number
    try:
        buttonSerial = serial.Serial(port)
        connected = True
    except serial.SerialException:
        port_number = port_number + 1

# If no port was valid, we should error out.
if connected:
	print "Button connected."
else:
    print "Button mode specified, but the button couldn't be found."
    sys.exit(-1)

# 2. turn on monitoring for 30 seconds
settings = {"consent_acquired": False,
            "recording": False}


def _set(setting, newValue):
	newValue = int(newValue)
	# For now limit new values to True or False.
	if newValue not in (True, False):
		raise ValueError("Settings must be either True or False.")

	# If we're not changing anything, don't do anything.
	if setting in settings.keys() and settings[setting] == newValue:
		return

	# When the consent status is changed, we need to reset the recording status.
	# TODO need to test and varify
	if setting == "consent_acquired":
		settings["consent_acquired"] = newValue
		_set("recording", newValue)
	elif setting == "recording":
		if settings["consent_acquired"] and newValue == True:
			settings["recording"] = True
			print "Kinect recorder start"
		else:
			settings["recording"] = False
			print "Kinect recorder stop"
            
            
def toggle(setting):
    if setting in settings.keys():
        oldValue = settings[setting]
        newValue = not oldValue
        _set(setting, newValue)
        return settings[setting]

while(True):
	time.sleep(0.25)
	if buttonSerial.inWaiting() > 0:
		print "Button incoming:"
		value = buttonSerial.read()
		print "Button value:%s" % value
		if value == 'c':
			setting = "consent_acquired"
		elif value == 'r':
			setting = "recording"
		else:
			raise Exception("Received erroneous data from the button.")
		print "Button mode: %s" % setting
		newValue = toggle(setting)
		buttonSerial.write("%d" % newValue)
		print settings




# 3. turn off monitoring 

