from time import time, sleep, localtime, strftime

import Adafruit_BMP.BMP085 as BMP085

def main():
	while True:
		print "Pressure: " + str(read_avg_pressure(100)) + "mbar"
		sleep(10)

def read_pressure():
	sensor = BMP085.BMP085()

	pressure = sensor.read_pressure()
	pressure = float(pressure)/100

	return pressure

def read_avg_pressure(count=1):
	sensor = BMP085.BMP085()

	sum = 0
	for i in range(count):
		pressure = sensor.read_pressure()
		pressure = float(pressure)/100
		sum += pressure
	
	sum /= count
	
	return sum

if __name__ == '__main__':
	main()