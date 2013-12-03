#import http.client
import httplib
from time import sleep, localtime, strftime
import sys

ARDUINO_NOT_READY = -9999

ip_addr = '192.168.xxx.xxx'
port = 80
timeout = 5
retry = 5


def main():
	while 1:
		temp = getArduinoTemp(ip_addr, port, timeout, retry)
		if (temp != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Arduino Temp\t" + str(temp))

		sleep(5)


def getArduinoTemp(ip_addr, port, timeout, retry):
	for i in range(retry):
		try:
			#conn = http.client.HTTPConnection(ip_addr, port, timeout)
			conn = httplib.HTTPConnection(ip_addr, port, timeout)
			conn.request("GET", "/temp")
			conn.sock.settimeout(timeout)
			r1 = conn.getresponse()
			if (r1.status == 200):
				lines = r1.read()
				line = lines.split('\n')
				temp = None
				if (len(lines.split()) == 3):
					temp = float(line[2])
				if (temp == ARDUINO_NOT_READY):
					temp = None
				else:
					break
			else:
				print (r1.status, r1.reason)
				temp = None
	
		except:
			print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
			temp = None
			sleep(2)	#wait for device to get ready again
		
	conn.close()

	return temp
	
if __name__ == "__main__":
	main()
	
