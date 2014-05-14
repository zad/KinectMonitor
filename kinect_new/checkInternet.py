import urllib2
import os

def internetOn():
    try:
    	response = urllib2.urlopen('http://74.125.228.100', timeout=1)
    	print "internetOn"
    	return True
    except urllib2.URLError as err:
    	print "internetOff"
    	return False

def reboot():
	os.system("echo Mvrvo5587 | sudo -S shutdown now -r")

if not internetOn():
    reboot()
