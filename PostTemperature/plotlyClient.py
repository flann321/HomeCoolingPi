import plotly
import sys
from tempodb import Client, DataPoint
from time import sleep, localtime, strftime
from datetime import datetime, timedelta
from random import random, randint

#Plotly credentials
plotly_un = 'username'
plotly_key = 'api_key'

#Tempodb credentials
api_key = "api_key"
api_secret = "api_secret"

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
  "title" : "Home Temperature",

 'titlefont': { 
	'family':fontlist,
	'size': 25,
	'color': "black"
	},

'autosize': True, 
'width': 880, 
'height': 500, 
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
  },

  "yaxis": {
	"title": "Temperature (F)",
	"titlefont": {
	  "family": fontlist,
	  "size": 18,
	  "color": "black"
	},
  },

  "paper_bgcolor": "white",
  "plot_bgcolor": "white",

  "showlegend": True,
  "legend": legendstyle,
  
  
   'annotations':
	[
   		{
		   'text':"<i><b>View the code used</b></i><i><b> to generate this plot <a href = 'https://github.com/flann321/HomeCoolingPi'> here</a></b></i>",
		   'x':1.0,
		   'y':-0.1,
		   'showarrow':False,
		   'ref':'paper',
		   'align':'left',
		   'font':{
					   'size':'12'
				   }

		},
	]
}


def main():
	global plotly_un, plotly_key
	global api_key, api_secret
	
	py = initPlotly(plotly_un, plotly_key)
	tempo = initTempodb(api_key, api_secret)
	if (py and tempo):	
		while(1):
			PostData(py, tempo)
			sleep(60*5)


def initPlotly(plotly_un, plotly_key):
	try:
		#Plotly handle
		py = plotly.plotly(username=plotly_un, key=plotly_key)
	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		return False

	return py


def initTempodb(api_key, api_secret):
	try:
		#Tempodb handle
		client = Client(api_key, api_secret)
	except:
		print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
		return False

	return client
	
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


def PostTempoData(py, client):

	try:
		dataread1 = client.read_key("temp1", datetime.now() - timedelta(days=2), datetime.now(), interval='raw')
		dataread2 = client.read_key("temp2", datetime.now() - timedelta(days=2), datetime.now(), interval='raw')
		dataread3 = client.read_key("temp3", datetime.now() - timedelta(days=2), datetime.now(), interval='raw')
		dataread4 = client.read_key("temp4", datetime.now() - timedelta(days=2), datetime.now(), interval='raw')
	
	#except:
	#	print (strftime("[%H:%M:%S]: EXCEPTION ", localtime()) + str(sys.exc_info()[0]))
	#	return False


		#Read and print whole series
		ts1 = []
		value1 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp1 dataset: " + str(len(dataread1.data)))
		for i in range(len(dataread1.data)):
			#print str(dataread1.data[i])
			ts1.append(str(dataread1.data[i].ts)[:19])

			temp = dataread1.data[i].value
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value1.append(temp)

		ts2 = []
		value2 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp2 dataset: " + str(len(dataread2.data)))
		for i in range(len(dataread2.data)):
			#print str(dataread2.data[i])
			ts2.append(str(dataread2.data[i].ts)[:19])

			temp = dataread2.data[i].value
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value2.append(temp)

		ts3 = []
		value3 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp3 dataset: " + str(len(dataread3.data)))
		for i in range(len(dataread3.data)):
			#print str(dataread3.data[i])
			ts3.append(str(dataread3.data[i].ts)[:19])

			temp = dataread3.data[i].value
			#temp = float('%.2f' % temp)		#Reduce to two digits
			value3.append(temp)

		ts4 = []
		value4 = []
		#print (strftime("[%H:%M:%S]: ", localtime()) + "temp4 dataset: " + str(len(dataread4.data)))
		for i in range(len(dataread4.data)):
			#print str(dataread4.data[i])
			ts4.append(str(dataread4.data[i].ts)[:19])

			temp = dataread4.data[i].value
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
	
