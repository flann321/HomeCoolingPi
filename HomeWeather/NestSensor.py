import sys
import os
import nest
from time import time, sleep, localtime, strftime
import hanging_threads
import threading
import signal
import traceback
import Queue
import FileLogger
import MySQLdatabase
from Credentials import *
from Config import *

nestsensor = None

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
	logger = FileLogger.startLogger("/var/log/NestSensor.log", 1000000, 5)
	logger.info("Starting Logger...")

	global nestsensor
	nestsensor = NestSensor(lock, qIn, qOut, logger)

	# Initialize NestSensor module
	if not nestsensor.init():
		print "Error: initializing NestSensor"
		sys.exit()

	#nestsensor.run()					# run on main thread
	nestsensor.start()					# start thread

	# Pass message to child
	msg = message()
	msg.timestamp = time()
	msg.command = "measure:temp?"
	msg.argument = ""
	qIn.put(msg)

	msg = message()
	msg.timestamp = time()
	msg.command = "measure:humidity?"
	msg.argument = ""
	qIn.put(msg)

	# Monitor for messages from child
	while True:
		if not qOut.empty():
			msg = qOut.get()
			if isinstance(msg, message):
				print (strftime("[%H:%M:%S]: ", localtime()) + "Message from NestSensor\t" + str(msg.command) +"\t" + str(msg.argument))
				logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Message from NestSensor\t" + str(msg.command) +"\t" + str(msg.argument))
		sleep(0.1)

	nestsensor.join()
	
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
	global nestsensor
	if nestsensor:
		nestsensor.stop()
	
class NestSensor(threading.Thread):
	""" Read Nest sensor data at defined interval and posts to database
		Latest reading can be queried through queue

		Ask the thread to stop by calling its stop() method.
    """
	def __init__(self, lock, qIn=None, qOut=None, logger=None):
		super(NestSensor, self).__init__()
		self.lock = lock
		self.qIn = qIn										# Incoming messages
		self.qOut = qOut									# Outgoing messages
		self.logger = logger								# Output log
		self.stoprequest = threading.Event()				# Stop thread flag

		self.postinterval = NestSensor_postinterval			# Save data interval
		self.retries = nest_retry

	def init(self):

		try:
			n = nest.Nest(nest_login, nest_passwd)
			n.login()
			return n
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())
			if self.logger:
				self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)

			return False
	

	def run(self):
		print "Starting NestSensor thread..."

		# Initialize
		self.n = self.init()
		if not self.n:
			print (strftime("[%H:%M:%S]: Error: cannot initialize Nest Sensor ", localtime()))
			if self.logger:
				self.logger.error(strftime("[%H:%M:%S]: Error: cannot initialize Nest Sensor ", localtime()), exc_info=True)
			return

		# Subtract post interval to get immediate reading in loop below
		currentposttime = time() - self.postinterval

		curTime = None
		curNestTemp = None
		curNestHumidity = None

		while True:

			try:
				if self.stoprequest.isSet():
					break

				# Save current measurement to database
				if (time() - currentposttime) > self.postinterval:
					currentposttime = time()

					self.lock.acquire()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "NestSensor lock acquired")

					try:
		
						db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
						
						if self.logger:
							self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Nest Reading")

						if (self.read_data(self.n, self.retries)):

							if self.logger:
								self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Nest Reading Done")

							curTime = time()

							curNestTemp = self.read_curtemp(self.n)
							if (curNestTemp != None):
								print (strftime("[%H:%M:%S]: ", localtime()) + "1st Floor Temp\t" + str(curNestTemp))

								if self.logger:
									self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Nest Reading Done")


								MySQLdatabase.InsertData(db, 'sensordata', '1st Floor', 'Nest', 'Current', 'Temperature', curNestTemp, 'F')
								if self.logger:
									self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "1st Floor Temp\t" + str(curNestTemp))

							curNestHumidity = self.read_curhumidity(self.n)
							if (curNestHumidity != None):
								print (strftime("[%H:%M:%S]: ", localtime()) + "1st Floor Humidity\t" + str(curNestHumidity))
								MySQLdatabase.InsertData(db, 'sensordata', '1st Floor', 'Nest', 'Current', 'Humidity', curNestHumidity, '%')
								if self.logger:
									self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "1st Floor Humidity\t" + str(curNestHumidity))

							if self.logger:
								self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Nest Save To Database")

						MySQLdatabase.Close(db)

						self.sendMessage(curTime, 'NestSensor', 'measure:temp', curNestTemp)
						self.sendMessage(curTime, 'NestSensor', 'measure:humidity', curNestHumidity)

					except IOError, e:
						print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

						if self.logger:
							self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
						#sys.exit()
					

					self.lock.release()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "NestSensor lock released")

				# Check incoming message queue
				if self.qIn:
					while not self.qIn.empty():
						msg = self.qIn.get()
						if isinstance(msg, message):
							if msg.command == 'measure:temp?':
								self.sendMessage(curTime, 'NestSensor', 'measure:temp', curNestTemp)

							if msg.command == 'measure:humidity?':
								self.sendMessage(curTime, 'NestSensor', 'measure:humidity', curNestHumidity)

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


	def read_data(self, n, retries=1):

		# retry Nest login if error occurs retrieving data
		retryLogin = True
		for i in range(retries):
			try:
				n.get_status()
				retryLogin = False
			except AttributeError:
				n.login()

				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())
				print (strftime("[%H:%M:%S]: Failed to read Nest, trying to log in", localtime()))
				if self.logger:
					self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
					self.logger.error('Failed to read Nest, trying to log in', exc_info=True)

			except Exception, e:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())
				print (strftime("[%H:%M:%S]: Failed to read Nest, unknown error", localtime()))
				if self.logger:
					self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
					self.logger.error('Failed to read Nest, unknown error', exc_info=True)

			# return True if data received
			if not retryLogin: return True
		
		# return False if data not received in retry loop
		return False


	def stop(self, timeout=None):
		self.stoprequest.set()
		super(NestSensor, self).join(timeout)

			
	def sendMessage(self, time, source, command, argument):
		msgOut = message()
		msgOut.timestamp = time
		msgOut.source = source
		msgOut.command = command
		msgOut.argument = argument

		if self.qOut and not self.qOut.full():
			self.qOut.put(msgOut)


	def read_curtemp(self, n):
		if self.logger:
			self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Nest read_curtemp")

		try:
			curNestTemp = float(n.get_curtemp())
			return curNestTemp
			
		except Exception, e:
			if self.logger:
				self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
				self.logger.error('Failed to read Nest, unknown error', exc_info=True)
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())
			print('Failed to read Nest, unknown error')
			
			return None


	def read_curhumidity(self, n):
		try:
			curNestHumidity = float(n.get_curhumidity())
			return curNestHumidity
			
		except Exception, e:
			if self.logger:
				self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
				self.logger.error('Failed to read Nest, unknown error', exc_info=True)
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())
			print('Failed to read Nest, unknown error')
			
			return None


class message:
	timestamp = None
	source = None
	command = None
	argument = None


if __name__ == '__main__':
	main()
