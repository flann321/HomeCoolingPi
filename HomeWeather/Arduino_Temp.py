import sys
import os
import httplib
import socket
import timeoutsocket
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

arduino_temp = None

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
	logger = FileLogger.startLogger("/var/log/Arduino_Temp.log", 1000000, 5)
	logger.info("Starting Logger...")


	global arduino_temp
	arduino_temp = Arduino_Temp(lock, qIn, qOut, logger)

	# Initialize Arduino_Temp module
	if not arduino_temp.init():
		print "Error: initializing Arduino_Temp"
		sys.exit()

	#arduino_temp.run()					# run on main thread
	arduino_temp.start()				# start thread

	# Pass message to child
	msg = message()
	msg.timestamp = time()
	msg.command = "measure:temp?"
	msg.argument = ""
	qIn.put(msg)

	# Monitor for messages from child
	while True:
		if not qOut.empty():
			msg = qOut.get()
			if isinstance(msg, message):
				print (strftime("[%H:%M:%S]: ", localtime()) + "Message from Arduino_Temp\t" + str(msg.command) +"\t" + str(msg.argument))
				logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Message from Arduino_Temp\t" + str(msg.command) +"\t" + str(msg.argument))
		sleep(0.1)

	arduino_temp.join()
	
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
	global arduino_temp
	if arduino_temp:
		arduino_temp.stop()
	
class Arduino_Temp(threading.Thread):
	""" Read Arduino temperature sensor at defined interval and posts to database
		Latest reading can be queried through queue

		Ask the thread to stop by calling its stop() method.
    """
	ARDUINO_NOT_READY = -9999

	def __init__(self, lock, qIn=None, qOut=None, logger=None):
		super(Arduino_Temp, self).__init__()
		self.lock = lock
		self.qIn = qIn										# Incoming messages
		self.qOut = qOut									# Outgoing messages
		self.logger = logger								# Output log
		self.stoprequest = threading.Event()				# Stop thread flag

		self.postinterval = ArduinoTemp_postinterval		# Save data interval

	def init(self):

		try:		
			temp = self.getArduinoTemp(arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry)
			if temp == None: return False
			else: return True

		except IOError, e:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

			if self.logger:
				self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
			sys.exit()
		

	def run(self):
		print "Starting Arduino Temp thread..."

		# Subtract post interval to get immediate reading in loop below
		currentposttime = time() - self.postinterval

		curTime = None
		curTemp = None

		while True:

			try:
				if self.stoprequest.isSet():
					break

				# Save current measurement to database
				if (time() - currentposttime) > self.postinterval:
					currentposttime = time()

					self.lock.acquire()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Arduino lock acquired")

					try:
		
						db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)

						if self.logger:
							self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Arduino Reading")
	
						curTime = time()

						curTemp = self.getArduinoTemp(arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry)
						if (curTemp != None):
							print (strftime("[%H:%M:%S]: ", localtime()) + "Arduino Temp\t" + str(curTemp))
							if self.logger:
								self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Attic Temp \t" + str(curTemp))
							MySQLdatabase.InsertData(db, 'sensordata', 'Attic', 'Arduino', 'Current', 'Temperature', curTemp, 'F')

						if self.logger:
							self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Debug Arduino Reading Done")

						MySQLdatabase.Close(db)

					except IOError, e:
						print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

						if self.logger:
							self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
						sys.exit()
					

					self.sendMessage(curTime, 'Arduino_Temp', 'measure:temp', curTemp)

					self.lock.release()
					if self.logger:
						self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "Arduino lock released")

				# Check incoming message queue
				if self.qIn:
					while not self.qIn.empty():
						msg = self.qIn.get()
						if isinstance(msg, message):
							if msg.command == 'measure:temp?':
								self.sendMessage(curTime, 'Arduino_Temp', 'measure:temp', curTemp)
						else:
							print "Error: unknown object in queue"
							if self.logger:
								self.logger.error(strftime("[%H:%M:%S]: ", localtime()) + "Error: unknown object in queue")
									
				sleep(0.1)				

			except Exception, e:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

				if self.logger:
					self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)
				sys.exit()


	def stop(self, timeout=None):
		self.stoprequest.set()
		super(Arduino_Temp, self).join(timeout)


	def sendMessage(self, time, source, command, argument):
		msgOut = message()
		msgOut.timestamp = time
		msgOut.source = source
		msgOut.command = command
		msgOut.argument = argument

		if self.qOut and not self.qOut.full():
			self.qOut.put(msgOut)


	def getArduinoTemp(self, ip_addr, port, timeout, retry):
		for i in range(retry):
			try:
				#conn = http.client.HTTPConnection(ip_addr, port, timeout)

				if self.logger:
					self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "getArduinoTemp HTTP connection")

				conn = httplib.HTTPConnection(ip_addr, port, timeout)

				if self.logger:
					self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "getArduinoTemp request")

				conn.request("GET", "/temp")
				conn.sock.settimeout(timeout)
				socket.setdefaulttimeout(timeout)
				timeoutsocket.setDefaultSocketTimeout(timeout)

				if self.logger:
					self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "getArduinoTemp get response")

				try:
					r1 = conn.getresponse()
				except socket.timeout:
					print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

					if self.logger:
						self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)

					temp = None
					continue

				if self.logger:
					self.logger.info (strftime("[%H:%M:%S]: ", localtime()) + "getArduinoTemp check response")

				if (r1.status == 200):
					lines = r1.read()
					line = lines.split('\n')
					temp = None
					if (len(lines.split()) == 3):
						temp = float(line[2])
					if (temp == self.ARDUINO_NOT_READY):
						temp = None
					else:
						break
				else:
					print (r1.status, r1.reason)
					temp = None
	
			except:
				print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc())

				if self.logger:
					self.logger.error((strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + traceback.format_exc()), exc_info=True)

				temp = None
				sleep(2)	#wait for device to get ready again
		
		conn.close()

		return temp

class message:
	timestamp = None
	source = None
	command = None
	argument = None


if __name__ == '__main__':
	main()