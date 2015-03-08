 #!/usr/bin/python
 # -*- coding: utf-8 -*-

import plotly
from plotly.graph_objs import *
import sys
import traceback
import MySQLdatabase
from time import sleep, time, localtime, strftime
from datetime import datetime, timedelta
from random import random, randint
from Credentials import *
from Config import *

#disable MySQL warnings
#from warnings import filterwarnings
#import MySQLdb as Database
#filterwarnings('ignore', category = Database.Warning)

debug = False

fontlist = '\"Avant Garde\", Avantgarde, \"Century Gothic\", CenturyGothic, \"AppleGothic\", sans-serif'

legendstyle = {
	"bgcolor": 'rgba(0, 0, 0, 0)',	#transparent
	"bordercolor": 'rgba(0, 0, 0, 0)',	#transparent
	"borderwidth": 0,
	"font":{
		'family': fontlist,
		'size': 12,
		'color': 'black'
	}
}

layout = {
  "title" : "Home Weather",

 'titlefont': { 
	'family':fontlist,
	'size': 25,
	'color': "black"
	},

'autosize': True, 
'width': 1000, 
'height': 900, 
'margin':{
	'l': 80,
	'r': 170,
	't': 80,
	'b': 80,
	'pad': 2 
	}, 

#global font
'font': {
  'family': fontlist,
  'size': 12,
  'color': "black"
  },
  
  "xaxis": {
	"title": "Time",
	"titlefont": {
	  "family": fontlist,
	  "size": 18,
	  "color": "black"
	},
	"anchor": "y3",
  },

  "yaxis": {
	"domain": [0.5, 1.0],
	"title": "Temperature (F)",
	"titlefont": {
	  "family": fontlist,
	  "size": 18,
	  "color": "black"
	},
  },

  "yaxis2": {
	"domain": [0.25, 0.5],
	"title": "Humidity / Cloud Cover (%)",
	"titlefont": {
	  "family": fontlist,
	  "size": 18,
	  "color": "black"
	},
	"anchor": "free",
	"overlaying": "none",
	"side": "right",
	"position": 1,
  },

  "yaxis3": {
	"domain": [0, 0.25],
	"title": "Pressure (mbar)",
	"titlefont": {
	  "family": fontlist,
	  "size": 18,
	  "color": "black"
	},
	"anchor": "free",
	"overlaying": "none",
	"side": "left",
  },

  "paper_bgcolor": "white",
  "plot_bgcolor": "white",

  "showlegend": True,
  "legend": legendstyle,
  
  
   'annotations': [	]
}

annotation_link = {
	'text':"<i><b>View the code used</b></i><i><b> to generate this plot <a href = 'https://github.com/flann321/HomeCoolingPi'> here</a></b></i>",
	'x':1.0,
	'y':-0.05,
	'showarrow':False,
	'ref':'paper',
	'align':'left',
	'font':{
			   'size':'12'
		   }
}

annotation_template = {
	'text':"",
	'bordercolor':"rgba(0, 0, 0, 0)",
	'borderwidth':2.9,
	'borderpad':1,
	'bgcolor':"rgba(0, 0, 0, 0)",
	'xref':"x",
	'yref':"y",
	'showarrow':True,
	'arrowwidth':2,
	'arrowcolor':"",
	'arrowhead':1,
	'arrowsize':1,
	'textangle':0,
	'tag':"",
	'font':{
		'family':"",
		'size':20,
		'color':"rgb(0, 0, 0)"
	},
	'opacity':1,
	'align':"center",
	'xanchor':"auto",
	'yanchor':"auto",
	'y':0,
	'x':0,
	'ay':0,
	'ax':0
}

annot1 = {'opacity': 1, 'yanchor': 'auto', 'text': '\xe2\x98\x80\xef\xb8\x8e', 'arrowsize': 1, 'tag': '', 'borderwidth': 2.9, 'ay': 0, 'ax': 0, 'font': {'color': 'rgb(0, 0, 0)', 'family': '', 'size': 20}, 'arrowcolor': '', 'xref': 'x', 'arrowhead': 1, 'bgcolor': 'rgba(0, 0, 0, 0)', 'borderpad': 1, 'showarrow': True, 'bordercolor': 'rgba(0, 0, 0, 0)', 'xanchor': 'auto', 'arrowwidth': 2, 'yref': 'y', 'align': 'center', 'textangle': 0, 'y': 95.905, 'x': 1410701712000.0}
annot2 = {'opacity': 1, 'yanchor': 'auto', 'text': '\xe2\x98\x80\xef\xb8\x8e', 'arrowsize': 1, 'tag': '', 'borderwidth': 2.9, 'ay': 0, 'ax': 0, 'font': {'color': 'rgb(0, 0, 0)', 'family': '', 'size': 20}, 'arrowcolor': '', 'xref': 'x', 'arrowhead': 1, 'bgcolor': 'rgba(0, 0, 0, 0)', 'borderpad': 1, 'showarrow': True, 'bordercolor': 'rgba(0, 0, 0, 0)', 'xanchor': 'auto', 'arrowwidth': 2, 'yref': 'y', 'align': 'center', 'textangle': 0, 'y': 95.905, 'x': 1410660135000.0}

def main():
	global plotly_un, plotly_key
	
	if debug: print strftime("[%H:%M:%S]: ", localtime()) + "Starting plotly Client..."	
	
	# Init plotly handle
	if debug: print strftime("[%H:%M:%S]: ", localtime()) + "initPlotly"
	py = initPlotly(plotly_un, plotly_key)

	while True:
		# Init MySQLdb
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "MySQL connect"
		db = MySQLdatabase.Connect(mysql_host, mysql_login, mysql_pw, mysql_db)
		if (db == None):
			return

		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "Post SQL data to plotly"
		starttime = time()
		PostArraySQL(py, db, plotlyInterval)
		endtime = time()
		print strftime("[%H:%M:%S]: ", localtime()) + "Plotly post time %s sec" % (endtime-starttime)

		MySQLdatabase.Close(db)

		sleep(plotly_postinterval)

	return

def initPlotly(plotly_un, plotly_key):
	try:
		#Plotly credentials
		plotly.tools.set_credentials_file(username=plotly_un, api_key=plotly_key)
		#Plotly handle
		py = plotly.plotly
	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		return False

	return py


# Convert SQL query result into series data
def GenerateDataPoints(queryresult):
	ts = []
	value = []
	for entry in queryresult:
		ts.append(str(entry[MySQLdatabase.timestamp]))
		value.append(entry[MySQLdatabase.data])

	return (ts, value)

# Generate the sunrise/sunset times as annotation list
# Input the SQL query and annotation text
# Returns list of annotations if found
# else returns None
def GenerateSunAnnotation(queryresult, annot_text=None, y=0, color='black'):
	#print "Generate Sun Annotation"
	#print 'color: ' + color
	
	annot = []
	#del(annot)
	#annot = []
	
	suntimesdict = {}
	#del(suntimesdict)
	#suntimesdict = {}
	
	(ts, value) = GenerateDataPoints(queryresult)

	# add datapoints to dictionary
	for suntime in value:

		#print "suntime"
		#print suntime
		#print ts[0]
		#print ts[len(ts)-1]
		#print suntime >= ts[0]
		#print suntime <= ts[len(ts)-1]

		dtstart = datetime.strptime(ts[0], '%Y-%m-%d %H:%M:%S')
		dtend = datetime.strptime(ts[len(ts)-1], '%Y-%m-%d %H:%M:%S')
		dtsuntime = datetime.fromtimestamp(suntime)

		#print dtstart
		#print dtend
		#print dtsuntime

		# only add datapoints that are within the 
		# given query timestamps will be plotted
		if dtsuntime >= dtstart and dtsuntime <= dtend:
			suntimesdict[suntime] = None	

	#print "dictionary: "
	#print suntimesdict

	for suntime in suntimesdict.keys():
		#ts = datetime.fromtimestamp(int(suntime)).strftime('%Y-%m-%d %H:%M:%S')
		#print "suntimesdict loop"
		
		annotation = annotation_template.copy()	# must copy dictionary explicitly
		annotation['text'] = annot_text
		annotation['x'] = suntime * 1000	# multiply by 1000 for plotly
		annotation['y'] = y
		annotation['ax'] = 0
		annotation['ay'] = 0
		annotation['font']['color'] = color
		
		#debug code
		#print 'annotation'
		#print annotation

		annot.append(annotation)
	
	#debug code
	#print 'annot'
	#print annot
	
	if annot == []:
		return None
	else:
		return annot
	
			
#Post data from SQL queries and send to plotly
def PostArraySQL(py, db, interval):

	data = []

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "ForecastIO Temperature"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Outdoor', 'ForecastIO', 'Current', 'Temperature')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Outdoor Temperature (ForecastIO)',
		'x' : ts,
		'y' : value,
		'type' : 'scatter',
		'mode' : 'lines'
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "Nest Temperature"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, '1st Floor', 'Nest', 'Current', 'Temperature')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : '1st Floor Temperature (Nest)',
		'x' : ts,
		'y' : value,
		'type' : 'scatter',
		'mode' : 'lines'
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "RPi Temperature"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, '2nd Floor', 'Raspberry Pi', 'Current', 'Temperature')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : '2nd Floor Temperature (Raspberry Pi)',
		'x' : ts,
		'y' : value,
		'type' : 'scatter',
		'mode' : 'lines'
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "Arduino Temperature"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Attic', 'Arduino', 'Current', 'Temperature')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Attic Temperature (Arduino)',
		'x' : ts,
		'y' : value,
		'type' : 'scatter',
		'mode' : 'lines'
		}
	data.append(series)


	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "Nest Humidity"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, '1st Floor', 'Nest', 'Current', 'Humidity')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Indoor Humidity (Nest)',
		'x' : ts,
		'y' : value,
		'yaxis' : 'y2',
		'type' : 'scatter',
		'mode' : 'lines',
		'line' : {
			'color' : "rgb(153,0,255)",
			},
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "ForecastIO Humidity"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Outdoor', 'ForecastIO', 'Current', 'Humidity')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Outdoor Humidity (ForecastIO)',
		'x' : ts,
		'y' : value,
		'yaxis' : 'y2',
		'type' : 'scatter',
		'mode' : 'lines',
		'line' : {
			'color' : "rgb(0,255,0)",
			},
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "ForecastIO CloudCover"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Outdoor', 'ForecastIO', 'Current', 'CloudCover')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Cloud Cover (ForecastIO)',
		'x' : ts,
		'y' : value,
		'yaxis' : 'y2',
		'type' : 'scatter',
		'mode' : 'lines',
		'line' : {
			'color' : "rgb(23,190,207)",
			},
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "RPi Pressure"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, '2nd Floor', 'Raspberry Pi', 'Current', 'Pressure')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Indoor Pressure (Raspberry Pi)',
		'x' : ts,
		'y' : value,
		'yaxis' : 'y3',
		'type' : 'scatter',
		'mode' : 'lines',
		'line' : {
			'color' : "rgb(255,0,0)",
			},
		}
	data.append(series)

	try:
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "ForecastIO Pressure"
		result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Outdoor', 'ForecastIO', 'Current', 'Pressure')
		(ts, value) = GenerateDataPoints(result)
	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		logger.error('Failed to query to MySQLdb', exc_info=True)
	series = {
		'name' : 'Outdoor Pressure (ForecastIO)',
		'x' : ts,
		'y' : value,
		'yaxis' : 'y3',
		'type' : 'scatter',
		'mode' : 'lines',
		'line' : {
			'color' : "rgb(0,0,255)",
			},
		}
	data.append(series)

	try:

		'''
		layout['annotations'][:] = []				# empty out annotation array
		#layout['annotations'] += [annotation_link]

		#print "layout init"
		#print layout['annotations']


		query = """select max(data) from sensordata where ttimestamp > current_timestamp() - interval %s and sensor="Temperature";""" % interval
		max = MySQLdatabase.Query(db, query)
		query = """select min(data) from sensordata where ttimestamp > current_timestamp() - interval %s and sensor="Temperature";""" % interval
		min = MySQLdatabase.Query(db, query)

		# Annotate sunrise/sunset times in middle of temperature chart
		if min[0][0] != None and max[0][0] != None:
			mid = (max[0][0] - min[0][0])/2 + min[0][0]

			result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Outdoor', 'ForecastIO', 'Current', 'Sunrise')
			annot_sunrise = GenerateSunAnnotation(result, '☀', y=mid, color='rgb(255,215,0)') #☀︎☼
			if annot_sunrise != None:
				layout['annotations'] += annot_sunrise[:]
	
			#print "sunrise2"
			#print annot_sunrise

			#print "layout1"
			#print layout['annotations']
	
			result = MySQLdatabase.QueryDataInterval(db, 'sensordata', interval, 'Outdoor', 'ForecastIO', 'Current', 'Sunset')
			annot_sunset = GenerateSunAnnotation(result, '☀︎', y=mid, color='rgb(255,215,0)') #☀︎☼
			if annot_sunset != None:
				layout['annotations'] += annot_sunset[:]

			#print "sunrise3"
			#print annot_sunrise

			#print "sunset"
			#print annot_sunset
	
			#print "layout annot2"
			#print layout['annotations']
		'''

		# Send data to plotly
		if debug: print strftime("[%H:%M:%S]: ", localtime()) + "Plotly Post"
		fig = Figure(data=data, layout=layout)
		response = py.plot(fig, filename='myplot', fileopt='overwrite')

	except:
		print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + traceback.format_exc())
		#print (strftime("[%H:%M:%S]: PostArraySQL EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		
		logger.error('Failed to query to MySQLdb', exc_info=True)


	
#Post data from array of traces and send to plotly
#Array i=trace, j=datapoints, k=tuple timestamp, datapoint
def PostArrayData(py, array):

	try:

		#Read and print whole series
		ts1 = []
		value1 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp1 dataset: " + str(len(dataread1.data)))
		for i in range(len(array[0])):
			ts1.append(str(array[0][i][0]))

			temp = array[0][i][1]
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value1.append(temp)

		ts2 = []
		value2 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp2 dataset: " + str(len(dataread2.data)))
		for i in range(len(array[1])):
			ts2.append(str(array[1][i][0]))

			temp = array[1][i][1]
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value2.append(temp)

		ts3 = []
		value3 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp3 dataset: " + str(len(dataread3.data)))
		for i in range(len(array[2])):
			ts3.append(str(array[2][i][0]))

			temp = array[2][i][1]
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value3.append(temp)

		ts4 = []
		value4 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp4 dataset: " + str(len(dataread4.data)))
		for i in range(len(array[3])):
			ts4.append(str(array[3][i][0]))

			temp = array[3][i][1]
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value4.append(temp)

		#plotly timestamp format 2012-01-01 00:00:00
		#time series example https://plot.ly/~chris/467/

		series1 = {
		  'name' : '1st Floor (Nest)',
		  'x': ts1, 
		  'y': value1,
		  'type': 'scatter', 
		  'mode': 'lines'}

		series2 = {
		  'name' : 'Outdoor (wunderground.com)',
		  'x': ts2, 
		  'y': value2,
		  'type': 'scatter', 
		  'mode': 'lines'}

		series3 = {
		  'name' : '2nd Floor (Raspberry Pi)',
		  'x': ts3, 
		  'y': value3,
		  'type': 'scatter', 
		  'mode': 'lines'}

		series4 = {
		  'name' : 'Attic (Arduino)',
		  'x': ts4, 
		  'y': value4,
		  'type': 'scatter', 
		  'mode': 'lines'}

		data = [series2, series1, series3, series4]

		print (strftime("[%H:%M:%S]: ", localtime()))
		response = py.plot(data,\
			filename='myplot', \
			fileopt='overwrite',\
			layout=layout)
		#print (strftime("[%H:%M:%S]: ", localtime()) + "url: " + response['url'])
		#print (strftime("[%H:%M:%S]: ", localtime()) + "filename: " + response['filename'])

	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		return False



if __name__ == "__main__":
	main()
	
