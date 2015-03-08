import urllib2
import json
from time import sleep, localtime, strftime
import sys


# Forecast key
forecast_key = "325a67cffc10bcd532eb28ceb25ad2a3"
latitude = "33.7"
longitude = "-117.77"
retry = 5

def main():
	while 1:
		json = get_ForecastData(forecast_key, latitude, longitude, retry)
		if json == None:
			return
		
		temp = getCurrentTemperature(json)		
		if (temp != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(temp))

		time = getCurrentTime(json)		
		if (time != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Time\t" + str(time))

		pressure = getCurrentPressure(json)		
		if (pressure != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Pressure\t" + str(pressure))

		cloudcover = getCurrentCloudCover(json)		
		if (cloudcover != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Cloud Cover\t" + str(cloudcover))

		humidity = getCurrentHumidity(json)		
		if (cloudcover != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Humidity\t" + str(humidity))

		sleep(60)



def get_ForecastData(key, latitude, longitude, retries=5):

	#Get data from weather service
	#If exception occurs, retry a few times then quit
	for retry in range(retries):
		try:
			f = urllib2.urlopen('https://api.forecast.io/forecast/' + key + '/' + str(latitude) + ',' + str(longitude))
			json_string = f.read()
			parsed_json = json.loads(json_string)
			break
			
		except:
			e = sys.exc_info()[0]
			print (e)
			parsed_json = None
			sleep(0.1)
			raise

	if (f != None):
		f.close()

	return parsed_json

def getCurrentTemperature(parsed_json):
	try:
		data = parsed_json['currently']['temperature']
	
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

def getCurrentTime(parsed_json):
	try:
		data = parsed_json['currently']['time']
	
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

def getCurrentPressure(parsed_json):
	try:
		data = parsed_json['currently']['pressure']
	
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

def getCurrentCloudCover(parsed_json):
	try:
		data = parsed_json['currently']['cloudCover']
	
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

def getCurrentHumidity(parsed_json):
	try:
		data = parsed_json['currently']['humidity']
	
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

# Get sunrise time
# Pass in ForecastIO json file and day 0-7
# Output format: unix time
def getSunriseTime(parsed_json, day=0):
	try:
		data = parsed_json['daily']['data'][day]['sunriseTime']
		#data = datetime.datetime.fromtimestamp(data).strftime('%H:%M:%S')
		
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

# Get sunset time
# Pass in ForecastIO json file and day 0-7
# Output format: unix time
def getSunsetTime(parsed_json, day=0):
	try:
		data = parsed_json['daily']['data'][day]['sunsetTime']
		#data = datetime.datetime.fromtimestamp(data).strftime('%H:%M:%S')
		
	except:
		e = sys.exc_info()[0]
		print (e)
		data = None
		raise

	return data

if __name__ == "__main__":
	main()
	
