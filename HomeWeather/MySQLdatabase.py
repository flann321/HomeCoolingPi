#!/usr/bin/env python

import MySQLdb
import sys
from time import time, sleep, localtime, strftime

# Commands
settimezone = "select SET GLOBAL time_zone = 'America/Los_Angeles';"
createdb = "CREATE DATABASE IF NOT EXISTS home_automation;"
createtable = """CREATE TABLE IF NOT EXISTS sensordata (
	record_no INT AUTO_INCREMENT PRIMARY KEY, 
	ttimestamp TIMESTAMP, 
	zone TEXT, 
	source TEXT, 
	timeframe TEXT, 
	sensor TEXT, 
	data DOUBLE, 
	unit TEXT,
	notes TEXT,
	attachment TEXT
);"""

insertdata = """INSERT INTO %s (zone, source, timeframe, sensor, data, unit)
VALUES("%s", "%s", "%s", "%s", %.2f, "%s");"""

querydata = """SELECT * from %s where ttimestamp > current_timestamp() - interval %s and zone = "%s" and source = "%s" and timeframe = "%s" and sensor = "%s";"""
queryrecentdata = """SELECT max(ttimestamp), data from %s where ttimestamp > current_timestamp() - interval %s and zone = "%s" and source = "%s" and timeframe = "%s" and sensor = "%s";"""

# Database schema
record_no = 0
timestamp = 1
zone = 2
source = 3
timeframe = 4
sensor = 5
data = 6
unit = 7


# Sample commands
# SELECT * from sensordata where ttimestamp > current_timestamp() - interval 48 hour and zone = "1st Floor" and sensor = "temperature";
#
# INSERT INTO sensordata(zone, source, timeframe, sensor, data, unit)
# VALUES("1st Floor", "Nest", "Current", "Temperature", 81.0, "F");
#
# DROP TABLE IF EXISTS sensordata;
#
# DELETE FROM sensordata WHERE ttimestamp > current_timestamp() - interval 48 hour and unit="F";
#
# select avg(data) from sensordata where ttimestamp > current_timestamp() - interval 48 hour and sensor="Temperature";
# select min(data) from sensordata where ttimestamp > current_timestamp() - interval 48 hour and sensor="Temperature";
# select max(data) from sensordata where ttimestamp > current_timestamp() - interval 48 hour and sensor="Temperature";
#
# most recent data
# select max(ttimestamp), data from sensordata where source = "Raspberry Pi" and sensor="Temperature";
# SELECT max(ttimestamp), data from sensordata where ttimestamp > current_timestamp() - interval 1 hour and zone = "1st Floor" and source = "Nest" and timeframe = "Current" and sensor = "Temperature";

# API usage
# import MySQLdatabase
# db = MySQLdatabase.Connect('localhost', 'root', 'root', 'home_automation')
# MySQLdatabase.QueryRecentData(db, 'sensordata', '1 day', '1st Floor', 'Nest', 'Current', 'Temperature')
# MySQLdatabase.InsertData(db, 'sensordata', '1st Floor', 'Nest', 'Current', 'Temperature', 81.22, 'F')
# MySQLdatabase.QueryDataInterval(db, 'sensordata', '1 day', '1st Floor', 'Nest', 'Current', 'Temperature')
#
# query = """select min(data) from sensordata where ttimestamp > current_timestamp() - interval 48 hour and sensor="Temperature";"""
# result = MySQLdatabase.Query(db, query)


# Connect to MySQL database and return database handle
def Connect(host, login, pw, db):
	try:
		dbhandle = MySQLdb.connect(host, login, pw, db)
		dbhandle.cursor().execute(createtable)
		dbhandle.commit()

		return dbhandle
	except:	
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		return None

# Close database connection	
def Close(db):
	db.close()

# Function custom-tailored to enter data into home_automation.sensordata table	
def InsertData(db, table, zone, source, timeframe, sensor, data, unit):
	try:
		cmd = insertdata % (table, zone, source, timeframe, sensor, data, unit)
		db.cursor().execute(cmd)
		db.commit()

	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		print "Error: MySQL database is being rolled back"
		db.rollback()
		raise

# Function custom-tailored to query data into home_automation.sensordata table with time interval
def QueryDataInterval(db, table, interval, zone, source, timeframe, sensor):
	try:
		query = querydata % (table, interval, zone, source, timeframe, sensor)
		cursor = db.cursor()
		cursor.execute(query)
		return cursor.fetchall()

	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		print "Error: MySQL invalid query"
		raise

# Function most recent datapoint matching query parameters
# Returns tuple of timestamp and data
# Returns (None, None) if no result found
def QueryRecentData(db, table, interval, zone, source, timeframe, sensor):
	try:
		query = queryrecentdata % (table, interval, zone, source, timeframe, sensor)
		cursor = db.cursor()
		cursor.execute(query)
		return cursor.fetchall()[0]

	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		print "Error: MySQL invalid query"
		raise


def Command(db, cmd):
	try:
		db.cursor().execute(cmd)
		db.commit()

	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		print "Error: MySQL database is being rolled back"
		db.rollback()
		raise

def Query(db, query):
	try:
		cursor = db.cursor()
		cursor.execute(query)
		return cursor.fetchall()

	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		print "Error: MySQL invalid query"
		raise

