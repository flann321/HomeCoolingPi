import sys
import signal
from time import time, sleep, localtime, strftime
from datetime import datetime
from threading import Timer
import json
import requests
import FileLogger
import nest
import Arduino_Temp
import WU_Temp
import RPi_Temp
import RPi_Pressure
import ForecastIO
import plotlyClient
import MySQLdatabase
from Credentials import *
from Config import *

# Datapoints
CHARTTIME = 3600 * 24 * 2	# 2 days		

# Data arrays
#NestDataPoints = []
#ForecastIODataPoints = []
#WUDataPoints = []
#RPiDataPoints = []
#ArduinoDataPoints = []
#DataPoints = [NestDataPoints, ForecastIODataPoints, RPiDataPoints, ArduinoDataPoints]	



def main():

	
	# Start File Logger
	print "Starting Logger.."
	global logger
	logger = FileLogger.startLogger("/var/log/HomeWeather.log", 1000000, 5)
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
	#global tempo_client
	#tempo_client = init_tempo(tempo_key, tempo_secret)

	# Init MySQLdb
	db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
	if (db == None):
		
		cleanup()
		return

	#Start Plotly Timer
	print "Starting Plotly Timer..."
	global tPlotlyPeriod, tPlotly
	tPlotlyPeriod = 60 * 1
	py = plotlyClient.initPlotly(plotly_un, plotly_key)
	if py:	
		tPlotly = Timer(0, PlotlyTimer, [py, db])
		tPlotly.start()
	else:
		cleanup()
		return

	# Start Nest Timer
	print "Starting Nest Timer..."
	global n, tNestPeriod, tNest
	n = nest.Nest(nlogin, npasswd)
	n.login()
	tNestPeriod = 60 * 3
	tNest = Timer(0, NestTimer, [n, db])
	tNest.start()

	# Start WU Timer
	#print "Starting WU Timer..."
	#global tWUPeriod, tWU
	#tWUPeriod = 60 * 15
	#tWU = Timer(0, WUTimer, [db])
	#tWU.start()
	
	# Start ForecastIO Timer
	print "Starting ForecastIO Timer..."
	global tForecastIOPeriod, tForecastIO
	tForecastIOPeriod = 60 * 3
	tForecastIO = Timer(0, ForecastIOTimer, [db])
	tForecastIO.start()

	# Start Raspberry Pi Temp Timer
	print "Starting Raspberry Pi Timer..."
	global tRPiPeriod, tRPi
	tRPiPeriod = 60 * 3
	device_file = RPi_Temp.initTemp()
	if (device_file):
		tRPi = Timer(0, RPiTimer, [device_file, db])
		tRPi.start()

	# Start Arduino Timer
	print "Starting Arduino Timer..."
	global tArduinoPeriod, tArduino
	tArduinoPeriod = 60 * 3
	tArduino = Timer(0, ArduinoTimer, [db])
	tArduino.start()
	
	# Setup exit handlers
	signal.signal(signal.SIGTSTP, SIGTSTP_handler)
	signal.signal(signal.SIGINT, SIGINT_handler)
	
	# Wait for termination
	signal.pause()
	

def SIGTSTP_handler(signum, frame):
	print 'SDIGTSTP detected!'
	sys.exit(0)

def SIGINT_handler(signum, frame):
	print 'SIGINT detected!'
	sys.exit(0)


def PlotlyTimer(*args):

	try:

		print "Plotly Timer"

		global tPlotly, tPlotlyPeriod
		global logger

		py = args[0]
		db = args[1]

		#debug
		#print data
		#debug
		
		try:
			db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
			plotlyClient.PostArraySQL(py, db, plotlyInterval)
			MySQLdatabase.Close(db)
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			logger.error('Failed to write to Plotly', exc_info=True)

	except:
		logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))

	#Start next timer iteration
	if not hasattr(PlotlyTimer, "next_call"):
		PlotlyTimer.next_call = time()  # it doesn't exist yet, so initialize it
	PlotlyTimer.next_call += tPlotlyPeriod

	tPlotly = Timer(PlotlyTimer.next_call - time(), PlotlyTimer, args)
	tPlotly.start()


def NestTimer(*args):

	try:

		print "NestTimer"

		global tNest
		#global n, tNest, tNestPeriod
		#global NestDataPoints
		global logger
		global CHARTTIME
		global tNestPeriod

		n = args[0]
		db = args[1]

		# Get Nest Temp
		curNestTemp = None
		curNestHumidity = None
		
		# retry Nest login if error occurs retrieving data
		retryLogin = True
		for i in range(5):
			try:
				n.get_status()
				curNestTemp = float(n.get_curtemp())
				curNestHumidity = float(n.get_curhumidity())
				retryLogin = False
			except AttributeError:
				n.login()
				logger.error('Failed to read Nest, trying to log in', exc_info=True)
			except Exception, e:
				logger.error('Failed to read Nest, unknown error', exc_info=True)

			# break loop if we login okay
			if not retryLogin: break
			
		print (strftime("[%H:%M:%S]: ", localtime()) + "Downstair Temp\t" + str(curNestTemp))
		logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Downstair Temp\t" + str(curNestTemp))

		# debug
		#print "NestDataPoints: "
		#print NestDataPoints
		#NestDataPoints.append((datetime.now(), curNestTemp))
		#print localtime()
		#print datetime.now()
		#print curNestTemp
		#print len(NestDataPoints)
		# debug
		
		if (curNestTemp != None and curNestHumidity != None):
			try:
				db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
				MySQLdatabase.InsertData(db, 'sensordata', '1st Floor', 'Nest', 'Current', 'Temperature', curNestTemp, 'F')
				MySQLdatabase.InsertData(db, 'sensordata', '1st Floor', 'Nest', 'Current', 'Humidity', curNestHumidity, '%')
				MySQLdatabase.Close(db)

				#NestDataPoints.append((datetime.now(), curNestTemp))
				#shorten array to fit chart
				#if (len(NestDataPoints) > CHARTTIME/tNestPeriod):
				#	index = len(NestDataPoints) - CHARTTIME/tNestPeriod
				#	NestDataPoints = NestDataPoints[index:]	
				
				#data = [DataPoint(datetime.now(), curNestTemp)]
				#tempo_client.write_key("temp1", data)
				#data = [{ 'key':'temp1', 'v':curNestTemp}]
				#tempo_client.write_bulk(datetime.now(), data)
			except:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				logger.error('Failed to write to MySQLdb', exc_info=True)
		else:
			logger.error('Nest API did not return temperature', exc_info=True)
		
	except:
		logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))

	#Start next timer iteration
	if not hasattr(NestTimer, "next_call"):
		NestTimer.next_call = time()  # it doesn't exist yet, so initialize it
	NestTimer.next_call += tNestPeriod

	tNest = Timer(NestTimer.next_call - time(), NestTimer, args)
	tNest.start()



def WUTimer(*args):

	try:

		print "WUTimer"

		global tWU, tWUPeriod
		global wu_key, wu_state, wu_city, wu_retry
		#global WUDataPoints
		global logger
		global CHARTTIME
		global tWUPeriod

		db = args[0]

		#debug
		#print "WUDataPoints: "
		#print WUDataPoints
		#debug

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
				db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'WU', 'Current', 'Temperature', curWUTemp, 'F')
				MySQLdatabase.Close(db)

				#WUDataPoints.append((datetime.now(), curWUTemp))
				#shorten array to fit chart
				#if (len(WUDataPoints) > CHARTTIME/tWUPeriod):
				#	index = len(WUDataPoints) - CHARTTIME/tWUPeriod
				#	WUDataPoints = WUDataPoints[index:]	
				#data = [DataPoint(datetime.now(), curWUTemp)]
				#tempo_client.write_key("temp2", data)
				#data = [{ 'key':'temp2', 'v':curWUTemp}]
				#tempo_client.write_bulk(datetime.now(), data)
			except:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				logger.error('WU: Failed to write to MySQLdb', exc_info=True)

	except:
		logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))

	#Start next timer iteration
	if not hasattr(WUTimer, "next_call"):
		WUTimer.next_call = time()  # it doesn't exist yet, so initialize it
	WUTimer.next_call += tWUPeriod

	tWU = Timer(WUTimer.next_call - time(), WUTimer, args)
	tWU.start()


def ForecastIOTimer(*args):

	try:

		print "ForecastIOTimer"

		global tForecastIO, tForecastIOPeriod
		global forecast_key, forecast_lat, forecast_long
		global logger
		global CHARTTIME

		retry = 5

		db = args[0]

		#debug
		#print "ForecastIODataPoints: "
		#print ForecastIODataPoints
		#debug

		#Get Weather Station temp
		curForecastIOTemp = None
		try:
			json = ForecastIO.get_ForecastData(forecast_key, forecast_lat, forecast_long, retry)
			if json != None:
				curForecastIOTemp = ForecastIO.getCurrentTemperature(json)		
				curForecastIOHumidity = ForecastIO.getCurrentHumidity(json)		
				curForecastIOPressure = ForecastIO.getCurrentPressure(json)		
				curForecastIOCloudCover = ForecastIO.getCurrentCloudCover(json)	
				curSunriseTime = ForecastIO.getSunriseTime(json)
				curSunsetTime = ForecastIO.getSunsetTime(json)
				

		except Exception, e:
			print (strftime("[%H:%M:%S]: ForecastIO Read EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			logger.error('Failed to read ForecastIO', exc_info=True)

		if (curForecastIOTemp != None and \
			curForecastIOHumidity != None and \
			curForecastIOPressure != None and \
			curForecastIOCloudCover != None):

			print (strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(curForecastIOTemp))
			logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(curForecastIOTemp))

			try:
				
				db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Temperature', curForecastIOTemp, 'F')
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Humidity', 100*curForecastIOHumidity, '%')
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Pressure', curForecastIOPressure, 'mbar')
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'CloudCover', 100*curForecastIOCloudCover, '%')
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Sunrise', curSunriseTime, 'unixtime')
				MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Sunset', curSunsetTime, 'unixtime')
				MySQLdatabase.Close(db)

				#ForecastIODataPoints.append((datetime.now(), curForecastIOTemp))
				#shorten array to fit chart
				#if (len(ForecastIODataPoints) > CHARTTIME/tForecastIOPeriod):
				#	index = len(ForecastIODataPoints) - CHARTTIME/tForecastIOPeriod
				#	ForecastIODataPoints = ForecastIODataPoints[index:]	
			except:
				print (strftime("[%H:%M:%S]: ForecastIO SQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				logger.error('ForecastIO: Failed to write to MySQLdb', exc_info=True)

	except:
		logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))

	#Start next timer iteration
	if not hasattr(ForecastIOTimer, "next_call"):
		ForecastIOTimer.next_call = time()  # it doesn't exist yet, so initialize it
	ForecastIOTimer.next_call += tForecastIOPeriod

	tForecastIO = Timer(ForecastIOTimer.next_call - time(), ForecastIOTimer, args)
	tForecastIO.start()


def RPiTimer(*args):

	try:

		print "RPiTimer"

		global logger
		#global RPiDataPoints
		global CHARTTIME
		global tRPiPeriod
	
		device_file = args[0]
		db = args[1]

		#debug
		#print "RPiDataPoints: "
		#print RPiDataPoints
		#debug

		#Get RaspberryPi temp
		curRPiTemp = None
		curRPiPressure = None
		try:
			#print "RPi temp"
			curRPiTemp = RPi_Temp.read_temp(device_file, 5)
			#print "RPi pressure"
			curRPiPressure = RPi_Pressure.read_pressure()
			if (curRPiPressure < 900 or curRPiPressure > 1100): curRPiPressure = None
		except Exception, e:
			logger.error('Failed to read Raspberry Pi', exc_info=True)



		if (curRPiTemp != None and curRPiPressure != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Upstair Temp\t" + str(curRPiTemp))
			logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Upstair Temp\t" + str(curRPiTemp))

			try:
				db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
				MySQLdatabase.InsertData(db, 'sensordata', '2nd Floor', 'Raspberry Pi', 'Current', 'Temperature', curRPiTemp, 'F')
				MySQLdatabase.InsertData(db, 'sensordata', '2nd Floor', 'Raspberry Pi', 'Current', 'Pressure', curRPiPressure, 'mbar')
				MySQLdatabase.Close(db)

				#RPiDataPoints.append((datetime.now(), curRPiTemp))
				#shorten array to fit chart
				#if (len(RPiDataPoints) > CHARTTIME/tRPiPeriod):
				#	index = len(RPiDataPoints) - CHARTTIME/tRPiPeriod
				#	RPiDataPoints = RPiDataPoints[index:]	
				#data = [DataPoint(datetime.now(), curRPiTemp)]
				#tempo_client.write_key("temp3", data)
			except:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				logger.error(strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]), exc_info=True)

	except:
		logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))

	#Start next timer iteration
	if not hasattr(RPiTimer, "next_call"):
		RPiTimer.next_call = time()  # it doesn't exist yet, so initialize it
	RPiTimer.next_call += tRPiPeriod

	tRPi = Timer(RPiTimer.next_call - time(), RPiTimer, args)
	tRPi.start()



def ArduinoTimer(*args):

	try:

		print "ArduinoTimer"

		global arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry
		#global ArduinoDataPoints
		global logger
		global CHARTTIME
		global tArduinoPeriod

		db = args[0]

		#debug
		#print "ArduinoDataPoints: "
		#print ArduinoDataPoints
		#debug

		#Get Arduino temp
		curArduinoTemp = Arduino_Temp.getArduinoTemp(arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry)
		if (curArduinoTemp):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Attic Temp\t" + str(curArduinoTemp))
			logger.info(strftime("[%H:%M:%S]: ", localtime()) + "Attic Temp\t" + str(curArduinoTemp))

			try:
				db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
				MySQLdatabase.InsertData(db, 'sensordata', 'Attic', 'Arduino', 'Current', 'Temperature', curArduinoTemp, 'F')
				MySQLdatabase.Close(db)

				#ArduinoDataPoints.append((datetime.now(), curArduinoTemp))
				#shorten array to fit chart
				#if (len(ArduinoDataPoints) > CHARTTIME/tArduinoPeriod):
				#	index = len(ArduinoDataPoints) - CHARTTIME/tArduinoPeriod
				#	ArduinoDataPoints = ArduinoDataPoints[index:]	
				#data = [DataPoint(datetime.now(), curArduinoTemp)]
				#tempo_client.write_key("temp4", data)
			except:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				logger.error('Arduino: Failed to write to MySQLdb', exc_info=True)
	except:
		logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))

	#Start next timer iteration
	if not hasattr(ArduinoTimer, "next_call"):
		ArduinoTimer.next_call = time()  # it doesn't exist yet, so initialize it
	ArduinoTimer.next_call += tArduinoPeriod

	tArduino = Timer(ArduinoTimer.next_call - time(), ArduinoTimer, args)
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
	

def cleanup():
	print "Clean up..."
	return
	
	
if __name__ == "__main__":
	main()
	
