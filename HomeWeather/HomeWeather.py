import sys
import signal
import threading
import traceback
import Queue
from time import time, sleep, localtime, strftime
from datetime import datetime
from threading import Timer
import FileLogger
import NestSensor
import Arduino_Temp
import RPi_Temp
import RPi_Pressure
import ForecastIO
import plotlyClient
import MySQLdatabase
from Credentials import *
from Config import *


def main():
	
	# Start File Logger
	print "Starting Logger.."
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

	lock = threading.Lock()

	# Initialize sensors
	if not initSensors(lock, logger):
		cleanup()
		sys.exit()
	sleep(30)				# wait for sensors to initialize
	
	# Initialize plotly
	if not initPlotly(lock, logger):
		cleanup()
		sys.exit()

	# Setup exit handlers
	signal.signal(signal.SIGTSTP, SIGTSTP_handler)
	signal.signal(signal.SIGINT, SIGINT_handler)
	
	# Wait for termination
	signal.pause()
	

def initSensors(lock, logger=None):

	# Init MySQLdb
	db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
	if (db == None):
		print (strftime("[%H:%M:%S]: Error: Cannot connect to MySQL database", localtime()))
		if logger:
			logger.error(strftime("[%H:%M:%S]: Error: Cannot connect to MySQL database", localtime()), exc_info=True)
		return False

	# Arduino Temp Sensor
	qIn_Arduino = Queue.Queue()
	qOut_Arduino = Queue.Queue()

	if ArduinoTempEnable:
		arduino_temp = Arduino_Temp.Arduino_Temp(lock, qIn_Arduino, qOut_Arduino, logger)

		# Initialize Arduino_Temp module
		if not arduino_temp.init():
			print (strftime("[%H:%M:%S]: Error: initializing Arduino_Temp", localtime()))
			if logger:
				logger.error(strftime("[%H:%M:%S]: Error: initializing Arduino_Temp", localtime()), exc_info=True)
			return False

		#arduino_temp.run()					# run on main thread
		arduino_temp.start()				# start thread

		#sleep(5)

	# ForecastIO Data
	qIn_ForecastIO = Queue.Queue()
	qOut_ForecastIO = Queue.Queue()

	if ForecastIOEnable:
		forecastio = ForecastIO.ForecastIO(lock, qIn_ForecastIO, qOut_ForecastIO, logger)

		# Initialize ForecastIO module
		if not forecastio.init():
			print (strftime("[%H:%M:%S]: Error: initializing ForecastIO", localtime()))
			if logger:
				logger.error(strftime("[%H:%M:%S]: Error: initializing ForecastIO", localtime()), exc_info=True)
			return False

		#forecastio.run()					# run on main thread
		forecastio.start()					# start thread

		#sleep(5)

	# Nest Sensor Data
	qIn_NestSensor = Queue.Queue()
	qOut_NestSensor = Queue.Queue()

	if NestSensorEnable:
		nestsensor = NestSensor.NestSensor(lock, qIn_NestSensor, qOut_NestSensor, logger)

		# Initialize NestSensor module
		if not nestsensor.init():
			print (strftime("[%H:%M:%S]: Error: initializing NestSensor", localtime()))
			if logger:
				logger.error(strftime("[%H:%M:%S]: Error: initializing NestSensor", localtime()), exc_info=True)
			return False

		#nestsensor.run()					# run on main thread
		nestsensor.start()					# start thread

		#sleep(5)


	# RPi Pressure Sensor
	qIn_RPiPressure= Queue.Queue()
	qOut_RPiPressure = Queue.Queue()

	if RPiPressEnable:
		rpipressure = RPi_Pressure.RPi_Pressure(lock, qIn_RPiPressure, qOut_RPiPressure, logger)

		# Initialize RPi Pressure module
		if not rpipressure.init():
			print (strftime("[%H:%M:%S]: Error: initializing RPi Pressure", localtime()))
			if logger:
				logger.error(strftime("[%H:%M:%S]: Error: initializing RPi Pressure", localtime()), exc_info=True)
			return False

		#rpipressure.run()					# run on main thread
		rpipressure.start()					# start thread

		#sleep(5)


	# RPi Temp Sensor
	qIn_RPiTemp= Queue.Queue()
	qOut_RPiTemp = Queue.Queue()

	if RPiTempEnable:
		rpi_temp = RPi_Temp.RPi_Temp(lock, qIn_RPiTemp, qOut_RPiTemp, logger)

		# Initialize RPi_Temp module
		if not rpi_temp.init():
			print (strftime("[%H:%M:%S]: Error: initializing RPi Temp", localtime()))
			if logger:
				logger.error(strftime("[%H:%M:%S]: Error: initializing RPi Temp", localtime()), exc_info=True)
			return False

		#rpi_temp.run()					# run on main thread
		rpi_temp.start()					# start thread

		#sleep(5)

	return True


def initPlotly(lock, logger=None):
	qIn_plotly= Queue.Queue()
	qOut_plotly = Queue.Queue()

	if plotlyEnable:
		plotlyclient = plotlyClient.plotlyClient(lock, qIn_plotly, qOut_plotly, logger)

		# Initialize plotlyClient module
		if not plotlyclient.init():
			print (plotlyclient("[%H:%M:%S]: Error: initializing plotlyClient", localtime()))
			if logger:
				logger.error(strftime("[%H:%M:%S]: Error: initializing plotlyClient", localtime()), exc_info=True)
			return False

		#plotlyclient.run()					# run on main thread
		plotlyclient.start()				# start thread
	
	return True
	

def SIGTSTP_handler(signum, frame):
	print 'SDIGTSTP detected!'
	sys.exit(0)

def SIGINT_handler(signum, frame):
	print 'SIGINT detected!'
	sys.exit(0)
	

def cleanup():
	print "Clean up..."
	
	
if __name__ == "__main__":
	main()
	
