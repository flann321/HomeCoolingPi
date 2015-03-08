import sys
import time
import MySQLdatabase
import RPi_Pressure

from Credentials import *
from Config import *
from enum import Enum


FanControllerSM = Enum('Off', 'On', 'Wait', 'CheckApp', 'CheckSensor')

def main():
	print "Launching House Fan Controller..."

	CheckEquipment()

	while 1:
		curRPiPressure = RPi_Pressure.read_avg_pressure(10)
		time.sleep(0.1)

def CheckEquipment():
	print "Checking connection to equipment..."


def StateMachine():
	print "Starting state machine..."
	

def GetSensorData():

	db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_table)
	(ts1, 1stFloorTemp) = MySQLdatabase.QueryRecentData(db, mysql_table, '12 minute', '1st Floor', 'Nest', 'Current', 'Temperature')
	(ts2, 2ndFloorTemp) = MySQLdatabase.QueryRecentData(db, mysql_table, '12 minute', '2nd Floor', 'Raspberry Pi', 'Current', 'Temperature')
	(ts3, OutdoorTemp) = MySQLdatabase.QueryRecentData(db, mysql_table, '12 minute', 'Outdoor', 'ForecastIO', 'Current', 'Temperature')



if __name__ == '__main__':
	main()