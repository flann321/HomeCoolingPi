import sys
import signal
from time import time, sleep, localtime, strftime
from datetime import datetime
from threading import Timer
import json
import requests
import FileLogger
from Credentials import *
import nest
import Arduino_Temp
import WU_Temp
import RPi_Temp
import plotlyClient
from tempodb import Client, DataPoint




def main():
	
	# Start File Logger
	global logger
	logger = FileLogger.startLogger("/var/log/PostTemperature.log", 1000000, 5)
	logger.info("Starting Logger...")
	
	# Check for internet connection
	#URL = "http://www.google.com"
	#print "Checking for internet connection..."
	#logger.info("Checking for internet connection...")
	#for retry in range(10):
	#	try:
	#		response = requests.get(URL)
	#	except Exception as e:
	#		print "Failed to connect to Internet"
	#		print e
	#		logger.error("Failed to connect to Internet", exc_info=True)
	#		sleep(3)
	#	if response.ok:
	#		break
		

	# Init TempoDB
	global tempo_client
	tempo_client = init_tempo(tempo_key, tempo_secret)

	#Start Plotly Timer
	global tPlotlyPeriod, tPlotly
	tPlotlyPeriod = 60 * 1
	py = plotlyClient.initPlotly(plotly_un, plotly_key)
	if (py and tempo_client):	
		tPlotly = Timer(0, PlotlyTimer, [py, tempo_client])
		tPlotly.start()

	# Start Nest Timer
	global n, tNestPeriod, tNest
	n = nest.Nest(nlogin, npasswd)
	n.login()
	tNestPeriod = 60 * 5
	tNest = Timer(0, NestTimer)
	tNest.start()

	# Start WU Timer
	global tWUPeriod, tWU
	tWUPeriod = 60 * 15
	tWU = Timer(0, WUTimer)
	tWU.start()
	
	# Start Raspberry Pi Temp Timer
	global tRPiPeriod, tRPi
	tRPiPeriod = 60 * 5
	device_file = RPi_Temp.initTemp()
	if (device_file):
		tRPi = Timer(0, RPiTimer, [device_file])
		tRPi.start()

	# Start Arduino Timer
	global tArduinoPeriod, tArduino
	tArduinoPeriod = 60 * 5
	tArduino = Timer(0, ArduinoTimer)
	tArduino.start()
	
	# Setup exit handlers
	signal.signal(signal.SIGTSTP, SIGTSTP_handler)	#Thread stop detected
	signal.signal(signal.SIGINT, SIGINT_handler)	#Ctrl+C detected
	
	# Wait for termination
	signal.pause()
	

def SIGTSTP_handler(signum, frame):
	print 'SIGTSTP detected!'
	sys.exit(0)

def SIGINT_handler(signum, frame):
	print 'SIGINT detected!'
	sys.exit(0)


def PlotlyTimer(*args):

	global tPlotly, tPlotlyPeriod
	global logger

	py = args[0]
	tempo_client = args[1]

	try:
		plotlyClient.PostData(py, tempo_client)
	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to write to Plotly', exc_info=True)

	#Start next timer iteration
	if not hasattr(PlotlyTimer, "next_call"):
		PlotlyTimer.next_call = time()  # it doesn't exist yet, so initialize it
	PlotlyTimer.next_call += tPlotlyPeriod

	tPlotly = Timer(PlotlyTimer.next_call - time(), PlotlyTimer, args)
	tPlotly.start()


def NestTimer():

	global n, tNest, tNestPeriod
	global logger

	# Get Nest Temp
	curNestTemp = None
	try:
		n.get_status()
		curNestTemp = float(n.get_curtemp())
	except Exception, e:
		logger.error('Failed to read Nest Temp', exc_info=True)

	if (curNestTemp != None):
		print (strftime("[%H:%M:%S]: ", localtime()) + "Downstair Temp\t" + str(curNestTemp))
		logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Downstair Temp\t" + str(curNestTemp))

		try:
			data = [DataPoint(datetime.now(), curNestTemp)]
			tempo_client.write_key("temp1", data)
			#data = [{ 'key':'temp1', 'v':curNestTemp}]
			#tempo_client.write_bulk(datetime.now(), data)
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			logger.error('Failed to write to TempoDB', exc_info=True)

	#Start next timer iteration
	if not hasattr(NestTimer, "next_call"):
		NestTimer.next_call = time()  # it doesn't exist yet, so initialize it
	NestTimer.next_call += tNestPeriod

	tNest = Timer(NestTimer.next_call - time(), NestTimer)
	tNest.start()


def WUTimer():

	global tWU, tWUPeriod
	global wu_key, wu_state, wu_city, wu_retry
	global logger

	#Get Weather Station temp
	curWUTemp = None
	try:
		curWUTemp = WU_Temp.get_WUTemp(wu_key, wu_state, wu_city, wu_retry)
	except Exception, e:
		logger.error('Failed to read WU Temp', exc_info=True)

	if (curWUTemp != None):
		print (strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(curWUTemp))
		logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(curWUTemp))

		try:
			data = [DataPoint(datetime.now(), curWUTemp)]
			tempo_client.write_key("temp2", data)
			#data = [{ 'key':'temp2', 'v':curWUTemp}]
			#tempo_client.write_bulk(datetime.now(), data)
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			logger.error('Failed to write to TempoDB', exc_info=True)

	#Start next timer iteration
	if not hasattr(WUTimer, "next_call"):
		WUTimer.next_call = time()  # it doesn't exist yet, so initialize it
	WUTimer.next_call += tWUPeriod

	tWU = Timer(WUTimer.next_call - time(), WUTimer)
	tWU.start()


def RPiTimer(*args):
	global logger
	
	device_file = args[0]

	#Get RaspberryPi temp
	curRPiTemp = None
	try:
		curRPiTemp = RPi_Temp.read_temp(device_file, 5)
	except Exception, e:
		logger.error('Failed to read Raspberry Pi Temp', exc_info=True)

	if (curRPiTemp != None):
		print (strftime("[%H:%M:%S]: ", localtime()) + "Upstair Temp\t" + str(curRPiTemp))
		logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Upstair Temp\t" + str(curRPiTemp))

		try:
			data = [DataPoint(datetime.now(), curRPiTemp)]
			tempo_client.write_key("temp3", data)
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			logger.error('Failed to write to TempoDB', exc_info=True)

	#Start next timer iteration
	if not hasattr(RPiTimer, "next_call"):
		RPiTimer.next_call = time()  # it doesn't exist yet, so initialize it
	RPiTimer.next_call += tRPiPeriod

	tRPi = Timer(RPiTimer.next_call - time(), RPiTimer, args)
	tRPi.start()


def ArduinoTimer():
	global arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry
	global logger

	#Get Arduino temp
	curArduinoTemp = Arduino_Temp.getArduinoTemp(arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry)
	if (curArduinoTemp):
		print (strftime("[%H:%M:%S]: ", localtime()) + "Attic Temp\t" + str(curArduinoTemp))
		logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Attic Temp\t" + str(curArduinoTemp))

		try:
			data = [DataPoint(datetime.now(), curArduinoTemp)]
			tempo_client.write_key("temp4", data)
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			logger.error('Failed to write to TempoDB', exc_info=True)

	#Start next timer iteration
	if not hasattr(ArduinoTimer, "next_call"):
		ArduinoTimer.next_call = time()  # it doesn't exist yet, so initialize it
	ArduinoTimer.next_call += tArduinoPeriod

	tArduino = Timer(ArduinoTimer.next_call - time(), ArduinoTimer)
	tArduino.start()


def init_tempo(api_key, api_secret):
	client = Client(api_key, api_secret)
	
	client.create_series('temp1')
	series1 = client.get_series(keys='temp1')
	if (len(series1) == 1):
		series1[0].tags = ["temp"]
		series1[0].attributes = {
			"source":"Thermostat",
			"description":"Nest",
			"location":"1st_Floor"
		}
		client.update_series(series1[0])
	
	client.create_series('temp2')
	series2 = client.get_series(keys='temp2')
	if (len(series2) == 1):
		series2[0].tags = ["temp"]
		series2[0].attributes = {
			"source":"Weather Station",
			"description":"Weather Underground",
			"city":"Northwood",
			"state":"CA",
			"location":"Outdoor"
		}
		client.update_series(series2[0])

	client.create_series('temp3')
	series3 = client.get_series(keys='temp3')
	if (len(series3) == 1):
		series3[0].tags = ["temp"]
		series3[0].attributes = {
			"source":"Temp Sensor",
			"description":"Raspberry Pi",
			"location":"2nd_Floor"
		}
		client.update_series(series3[0])

	client.create_series('temp4')
	series4 = client.get_series(keys='temp4')
	if (len(series4) == 1):
		series4[0].tags = ["temp"]
		series4[0].attributes = {
			"source":"Temp Sensor",
			"description":"Arduino",
			"location":"Attic"
		}
		client.update_series(series4[0])

	return client
	
	
	
if __name__ == "__main__":
	main()
	
