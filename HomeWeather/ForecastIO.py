import sys
from time import time, sleep, localtime, strftime
#import hanging_threads
import threading
import signal
import traceback
import Queue
import FileLogger
import MySQLdatabase
import urllib2
import json
from Credentials import *
from Config import *

forecastio = None

def main():

	# Setup exit handlers
	signal.signal(signal.SIGTSTP, SIGTSTP_handler)
	signal.signal(signal.SIGINT, SIGINT_handler)
	
	lock = threading.Lock()
	qIn = Queue.Queue()
	qOut = Queue.Queue()

	# Start File Logger
	print "Starting Logger.."
	global logger
	logger = FileLogger.startLogger("/var/log/ForecastIO.log", 1000000, 5)
	logger.info("Starting Logger...")

	global forecastio
	forecastio = ForecastIO(lock, qIn, qOut, logger)

	# Initialize ForecastIO module
	if not forecastio.init():
		print "Error: initializing ForecastIO"
		sys.exit()

	#forecastio.run()					# run on main thread
	forecastio.start()					# start thread

	# Pass message to child
	msg = message()
	msg.timestamp = time()
	msg.source = 'main'
	msg.command = "measure:temp?"
	msg.argument = ""
	qIn.put(msg)

	# Monitor for messages from child
	while True:
		if not qOut.empty():
			msg = qOut.get()
			if isinstance(msg, message):
				print (strftime("[%H:%M:%S]: ", localtime()) + "Message from ForecastIO\t" + str(msg.command) +"\t" + str(msg.argument))
				logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Message from ForecastIO\t" + str(msg.command) +"\t" + str(msg.argument))
		sleep(0.1)

	forecastio.join()
	
	# Wait for termination
	signal.pause()
	

def SIGTSTP_handler(signum, frame):
	print 'SDIGTSTP detected!'
	cleanup()
	sys.exit(0)

def SIGINT_handler(signum, frame):
	print 'SIGINT detected!'
	cleanup()
	sys.exit(0)

def cleanup():
	global forecastio
	if forecastio:
		forecastio.stop()
	
class ForecastIO(threading.Thread):
	""" Reads ForecastIO weather data at defined interval and posts to database
		Latest data can queried through queue

		Ask the thread to stop by calling its stop() method.
    """
	def __init__(self, lock, qIn=None, qOut=None, logger=None):
		super(ForecastIO, self).__init__()
		self.lock = lock
		self.qIn = qIn										# Incoming messages
		self.qOut = qOut									# Outgoing messages
		self.logger = logger								# Output log
		self.stoprequest = threading.Event()				# Stop thread flag

		self.postinterval = ForecastIO_postinterval			# Save data interval

	def init(self):
		try:
			# Got parameters from Config and Credentials files
			json = self.get_ForecastData(forecast_key, forecast_lat, forecast_long, forecast_retry)
			if json == None:
				return False
			else:
				return True
						
		except IOError, e:
			#print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

			if self.logger:
				#self.logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
			#sys.exit()
		

	def run(self):
		print "Starting ForecastIO thread..."

		# Initialize
		if not self.init():
			print (strftime("[%H:%M:%S]: Error: cannot initialize ForecastIO ", localtime()))

		# Subtract post interval to get immediate reading in loop below
		currentposttime = time() - self.postinterval

		curTemp = None
		curTime = None
		curPressure = None
		curCloudcover = None
		curHumidity = None
		curSunriseTime = None
		curSunsetTime = None

		while True:

			try:
				if self.stoprequest.isSet():
					break

				# Save ForecastIO data to database
				if (time() - currentposttime) > self.postinterval:
					currentposttime = time()

					self.lock.acquire()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "ForecastIO lock acquired")

					try:
						# Got parameters from Config and Credentials files
						json = self.get_ForecastData(forecast_key, forecast_lat, forecast_long, forecast_retry)
						if json == None:
							return
		
						db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)

						curTemp = self.getCurrentTemperature(json)		
						if (curTemp != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(curTemp))
							MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Temperature', curTemp, 'F')
							if self.logger:
								self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(curTemp))

						curTime = self.getCurrentTime(json)		
						if (curTime != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Time\t" + str(curTime))

						curPressure = self.getCurrentPressure(json)		
						if (curPressure != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Pressure\t" + str(curPressure))
							MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Pressure', curPressure, 'mbar')

						curCloudCover = self.getCurrentCloudCover(json)		
						if (curCloudCover != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Cloud Cover\t" + str(curCloudCover))
							MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'CloudCover', 100*curCloudCover, '%')

						curHumidity = self.getCurrentHumidity(json)		
						if (curHumidity != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Humidity\t" + str(curHumidity))
							MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Humidity', 100*curHumidity, '%')

						curSunriseTime = self.getSunriseTime(json)		
						if (curSunriseTime != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Sunrise Time\t" + str(curSunriseTime))
							MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Sunrise', curSunriseTime, 'unixtime')

						curSunsetTime = self.getSunsetTime(json)		
						if (curSunsetTime != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Sunset Time\t" + str(curSunsetTime))
							MySQLdatabase.InsertData(db, 'sensordata', 'Outdoor', 'ForecastIO', 'Current', 'Sunset', curSunsetTime, 'unixtime')

						MySQLdatabase.Close(db)

						self.sendMessage(curTime, 'ForecastIO', 'measure:temp', curTemp)
						self.sendMessage(curTime, 'ForecastIO', 'measure:pressure', curPressure)
						self.sendMessage(curTime, 'ForecastIO', 'measure:cloudcover', curCloudCover)
						self.sendMessage(curTime, 'ForecastIO', 'measure:humidity', curHumidity)
						self.sendMessage(curTime, 'ForecastIO', 'measure:sunrisetime', curSunriseTime)
						self.sendMessage(curTime, 'ForecastIO', 'measure:sunsettime', curSunsetTime)

					#except IOError, e:
					except Exception, e:
						#print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
						print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

						if self.logger:
							#self.logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
							self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)

					
					self.lock.release()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "ForecastIO lock released")


				# Check incoming message queue
				if self.qIn:
					while not self.qIn.empty():
						msg = self.qIn.get()
						if isinstance(msg, message):
							if msg.command == 'measure:temp?':
								msgOut = message()
								msgOut.timestamp = time()
								msgOut.source = 'ForecastIO'
								msgOut.command = 'measure:temp'
								msgOut.argument = curTemp

								if (self.qOut and not self.qOut.full()):
									self.qOut.put(msgOut)
						else:
							print "Error: unknown object in queue"
							if self.logger:
								self.logger.error(strftime("[%H:%M:%S]: ", localtime()) + "Error: unknown object in queue")
									
				sleep(0.1)				

			except Exception, e:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

				if self.logger:
					self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
				#sys.exit()


	def stop(self, timeout=None):
		self.stoprequest.set()
		super(ForecastIO, self).join(timeout)


	def sendMessage(self, time, source, command, argument):
		msgOut = message()
		msgOut.timestamp = time
		msgOut.source = source
		msgOut.command = command
		msgOut.argument = argument

		if self.qOut and not self.qOut.full():
			self.qOut.put(msgOut)


	def get_ForecastData(self, key, latitude, longitude, retries=5):

		#Get data from weather service
		#If exception occurs, retry a few times then quit
		for retry in range(retries):
			try:
				f = urllib2.urlopen('https://api.forecast.io/forecast/' + key + '/' + str(latitude) + ',' + str(longitude))
				json_string = f.read()
				parsed_json = json.loads(json_string)
				break
			
			except:
				e = sys.exc_info()[0]
				print (e)
				parsed_json = None
				sleep(0.1)
				raise

		if (f != None):
			f.close()

		return parsed_json

	def getCurrentTemperature(self, parsed_json):
		try:
			data = parsed_json['currently']['temperature']
	
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

	def getCurrentTime(self, parsed_json):
		try:
			data = parsed_json['currently']['time']
	
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

	def getCurrentPressure(self, parsed_json):
		try:
			data = parsed_json['currently']['pressure']
	
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

	def getCurrentCloudCover(self, parsed_json):
		try:
			data = parsed_json['currently']['cloudCover']
	
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

	def getCurrentHumidity(self, parsed_json):
		try:
			data = parsed_json['currently']['humidity']
	
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

	# Get sunrise time
	# Pass in ForecastIO json file and day 0-7
	# Output format: unix time
	def getSunriseTime(self, parsed_json, day=0):
		try:
			data = parsed_json['daily']['data'][day]['sunriseTime']
			#data = datetime.datetime.fromtimestamp(data).strftime('%H:%M:%S')
		
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

	# Get sunset time
	# Pass in ForecastIO json file and day 0-7
	# Output format: unix time
	def getSunsetTime(self, parsed_json, day=0):
		try:
			data = parsed_json['daily']['data'][day]['sunsetTime']
			#data = datetime.datetime.fromtimestamp(data).strftime('%H:%M:%S')
		
		except:
			e = sys.exc_info()[0]
			print (e)
			data = None
			raise

		return data

class message:
	timestamp = None
	source = None
	command = None
	argument = None


if __name__ == '__main__':
	main()