import os
import glob
import time
import sys
from time import time, sleep, localtime, strftime


def main():

	device_file = initTemp()
	if (device_file):
		while True:
			print(read_temp(device_file, 5))	
			sleep(1)


def initTemp():
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')

	base_dir = '/sys/bus/w1/devices/'

	try:
		device_folder = glob.glob(base_dir + '28*')[0]
	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		return False

	device_file = device_folder + '/w1_slave'

	return device_file
	

def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device_file, retries=0):
	for retry in range(retries):
		lines = read_temp_raw(device_file)
		if (lines[0].strip()[-3:] == 'YES'):
			break
		sleep(0.2)

	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_f
	else:
		return None
	

if __name__ == "__main__":
	main()
	
