
# Wemo switch
wemoSwitchName = "Whole House Fan"

# House Fan Control Settings
HouseFanControlEnable = True
tempDelta = 5							# Minimum indoor to outdoor temperature delta to start house fan
minIndoorTemp = 68						# Shut down house fan cooling below this indoor temp
maxOutdoorTemp = 75						# Shut down house fan cooling above this outdoor temp

# Plotly settings
plotlyEnable = True
#plotlyInterval = "2 day"				# Most recent interval of datapoint to display in integer days
plotlyIntervalDays = 2					# Most recent interval of datapoint to display in integer days
plotly_postinterval = 3*60				# Save data interval (sec)

# RPi Pressure Sensor
RPiPressEnable = True
RPiPressDropEnable = False
pressureDrop_mbar = 0.12				# Shut down house fan if pressure drops this much in short period of time
RPiPress_monLen = 20					# Recent measurement monitor array length
RPiPress_monitorinterval = 1			# Monitor sensor interval (sec)
RPiPress_postinterval = 3*60			# Save data interval (sec)
RPiPress_averaging = 10					# Number of samples to average
RPiPress_dataHigh = 1100				# Upper limit for valid data
RPiPress_dataLow = 900					# Lower limit for valid data

# RPi Temp Sensor
RPiTempEnable = True
RPiTemp_postinterval = 3*60				# Save data interval (sec)

# ForecastIO Settings
ForecastIOEnable = True
ForecastIO_postinterval = 3*60			# Save data interval (sec)

# Arduino Temp Sensor
ArduinoTempEnable = True
ArduinoTemp_postinterval = 3*60			# Save data interval (sec)

# Nest Sensor
NestSensorEnable = True
NestSensor_postinterval = 3*60			# Save data interval (sec)

