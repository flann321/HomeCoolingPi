import sys
from time import time, sleep, localtime, strftime
import hanging_threads
import threading
import signal
import traceback
import Queue
import FileLogger
import MySQLdatabase
import Adafruit_BMP.BMP085 as BMP085
from Credentials import *
from Config import *

rpipressure = None

def main():
#	while True:
#		print "Pressure: " + str(read_avg_pressure(100)) + "mbar"
#		sleep(10)

	# Setup exit handlers
	signal.signal(signal.SIGTSTP, SIGTSTP_handler)
	signal.signal(signal.SIGINT, SIGINT_handler)
	
	lock = threading.Lock()
	qIn = Queue.Queue()
	qOut = Queue.Queue()

	# Start File Logger
	print "Starting Logger.."
	global logger
	logger = FileLogger.startLogger("/var/log/RPi_Pressure.log", 1000000, 5)
	logger.info("Starting Logger...")

	global rpipressure
	rpipressure = RPi_Pressure(lock, qIn, qOut, logger)

	# Initialize RPi Pressure module
	if not rpipressure.init():
		print "Error: initializing RPi Pressure"
		sys.exit()

	#rpipressure.run()					# run on main thread
	rpipressure.start()					# start thread

	# Pass message to child
	msg = message()
	msg.timestamp = time()
	msg.command = "measure:pressure?"
	msg.argument = ""
	qIn.put(msg)

	# Monitor for messages from child
	while True:
		if not qOut.empty():
			msg = qOut.get()
			if isinstance(msg, message):
				print (strftime("[%H:%M:%S]: ", localtime()) + "Message from RPi Pressure\t" + str(msg.command) +"\t" + str(msg.argument))
				logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Message from RPi Pressure\t" + str(msg.command) +"\t" + str(msg.argument))
		sleep(0.1)

	rpipressure.join()
	
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
	global rpipressure
	if rpipressure:
		rpipressure.stop()
	
class RPi_Pressure(threading.Thread):
	""" Measures Raspberry Pi Pressure sensor at defined interval and post to database
		Queue message out when sudden pressure change detected

		Ask the thread to stop by calling its stop() method.
    """
	def __init__(self, lock, qIn=None, qOut=None, logger=None):
		super(RPi_Pressure, self).__init__()
		self.lock = lock
		self.qIn = qIn										# Incoming messages
		self.qOut = qOut									# Outgoing messages
		self.logger = logger								# Output log
		self.stoprequest = threading.Event()				# Stop thread flag

		self.pressureDrop = pressureDrop_mbar				# Pressure drop threshold (mbar)

		self.monArr = []									# Recent measurement monitor array
		self.monLen = RPiPress_monLen						# Recent measurement monitor array length
		self.monitorinterval = RPiPress_monitorinterval		# Monitor sensor interval

		self.postinterval = RPiPress_postinterval			# Save data interval

		self.averaging = RPiPress_averaging					# Number of samples to average
		self.dataHigh = RPiPress_dataHigh					# Upper limit for valid data
		self.dataLow = RPiPress_dataLow						# Lower limit for valid data

	def init(self):
		try:
			pressure = self.read_avg_pressure(self.averaging)
		except IOError, e:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			print 'Check that script ran from root user'

			if self.logger:
				self.logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				self.logger.error('Check that script ran from root user')
			sys.exit()
		

		if (pressure > self.dataLow and pressure < self.dataHigh):
			return True
		else:
			return False

	def run(self):
		print "Starting RPi Pressure thread..."

		currentmonitortime = time() - self.monitorinterval
		currentposttime = time() - self.postinterval
		
		curTime = None
		curRPiPressure = None

		while True:

			try:
				if self.stoprequest.isSet():
					break

				# Check for pressure drop
				if RPiPressDropEnable:
					if (time() - currentmonitortime) > self.monitorinterval:
						#print (strftime("[%H:%M:%S]: ", localtime()) + "check pressure drop")
						currentmonitortime = time()

						curTime = time()
						try:
							curRPiPressure = self.read_avg_pressure(self.averaging)
						except IOError, e:
							print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
							print 'Check that script ran from root user'

							if self.logger:
								self.logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
								self.logger.error('Check that script ran from root user')
							sys.exit()

						#print (strftime("[%H:%M:%S]: ", localtime()) + str(curRPiPressure))

						# Add measurement to FIFO
						self.monArr.append(curRPiPressure)
						while (len(self.monArr) > self.monLen):
							self.monArr.pop(0)
						# Detect pressure drop once queue is full
						if (len(self.monArr) == self.monLen):
							# Detect sudden pressure drop
							#drop = self.monArr[0] - min(self.monArr)
							halflen = len(self.monArr)/2
							fulllen = len(self.monArr)
							firsthalf = sum(self.monArr[0:halflen])/len(self.monArr[0:halflen])
							secondhalf = sum(self.monArr[halflen:fulllen])/len(self.monArr[halflen:fulllen])
							drop = firsthalf-secondhalf
							if (drop > self.pressureDrop):
								warning = strftime("[%H:%M:%S]: ", localtime()) + "Excessive pressure change detected: %s %s" % (str(drop), ''.join(str(self.monArr)))
								print warning
								if self.logger:
									self.logger.info(warning)

								self.sendMessage(curTime, 'RPi_Pressure', 'pressure drop', drop)


				# Save pressure to database
				if (time() - currentposttime) > self.postinterval:
					#print (strftime("[%H:%M:%S]: ", localtime()) + "save to database")
					currentposttime = time()

					self.lock.acquire()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "RPi_Pressure lock acquired")

					try:
						curRPiPressure = self.read_avg_pressure(self.averaging)
					except IOError, e:
						print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
						print 'Check that script ran from root user'

						if self.logger:
							self.logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
							self.logger.error('Check that script ran from root user')
						sys.exit()
					
					print (strftime("[%H:%M:%S]: ", localtime()) + "Indoor Pressure\t" + str(curRPiPressure))
					#if (curRPiPressure < self.dataLow or curRPiPressure > self.dataHigh): curRPiPressure = None

					db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
					MySQLdatabase.InsertData(db, 'sensordata', '2nd Floor', 'Raspberry Pi', 'Current', 'Pressure', curRPiPressure, 'mbar')
					MySQLdatabase.Close(db)

					self.sendMessage(curTime, 'RPi_Pressure', 'measure:pressure', curRPiPressure)

					self.lock.release()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "RPi_Pressure lock acquired")

				# Check incoming message queue
				if self.qIn:
					while not self.qIn.empty():
						msg = self.qIn.get()
						if isinstance(msg, message):
							if msg.command == 'measure:pressure?':
								self.sendMessage(curTime, 'RPi_Pressure', 'measure:pressure', curRPiPressure)
						else:
							print "Error: unknown object in queue"
							if self.logger:
								self.logger.error(strftime("[%H:%M:%S]: ", localtime()) + "Error: unknown object in queue")
									
				sleep(0.1)				

			except Exception, e:
				#print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

				if self.logger:
					#self.logger.error (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
					self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
				sys.exit()


	def stop(self, timeout=None):
		self.stoprequest.set()
		super(RPi_Pressure, self).join(timeout)


	def sendMessage(self, time, source, command, argument):
		msgOut = message()
		msgOut.timestamp = time
		msgOut.source = source
		msgOut.command = command
		msgOut.argument = argument

		if self.qOut and not self.qOut.full():
			self.qOut.put(msgOut)


	def read_pressure(self):
		sensor = BMP085.BMP085()

		pressure = sensor.read_pressure()
		pressure = float(pressure)/100

		return pressure

	def read_avg_pressure(self, count=1):
		sensor = BMP085.BMP085()

		sum = 0
		for i in range(count):
			pressure = sensor.read_pressure()
			pressure = float(pressure)/100
			sum += pressure
	
		sum /= count
	
		return sum

class message:
	timestamp = None
	source = None
	command = None
	argument = None


if __name__ == '__main__':
	main()