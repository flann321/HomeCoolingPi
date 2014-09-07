import urllib2
import json
from time import sleep, localtime, strftime
import sys


# Weather Underground key
wu_key = "key"
wu_state = "state"
wu_city = "city"
wu_retry = 5


def main():
	while 1:
		temp = get_WUTemp(wu_key, wu_state, wu_city, wu_retry)
		if (temp != None):
			print (strftime("[%H:%M:%S]: ", localtime()) + "Outdoor Temp\t" + str(temp))

		sleep(60)



def get_WUTemp(key, state, city, retries=5):

	#Get data from weather service
	#If exception occurs, retry a few times then quit
	for retry in range(retries):
		try:
			f = urllib2.urlopen('http://api.wunderground.com/api/' + key + '/geolookup/conditions/q/' + state + '/' + city + '.json')
			json_string = f.read()
			#print json_string
			parsed_json = json.loads(json_string)
			location = parsed_json['location']['city']
			temp_f = parsed_json['current_observation']['temp_f']
			#print "Current temperature in %s is: %s" % (location, temp_f)
		except:
			e = sys.exc_info()[0]
			print (e)
			temp_f = None
			sleep(0.1)
			raise

	if (f != None):
		f.close()

	return temp_f


if __name__ == "__main__":
	main()
	
