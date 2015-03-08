# Connect to Nest Thermostat
global nest_login, nest_passwd, nest_retry
nest_login = "login"
nest_passwd = "password"
nest_retry = 5

# Weather Underground key
global wu_key, wu_state, wu_city, wu_retry
wu_key = "wu_key"
wu_state = "2-letter state"
wu_city = "city"
wu_retry = 5

# Forecast IO key
global forecast_key, forecast_lat, forecast_long
forecast_key = "forecast_key"
forecast_lat = "latitude"
forecast_long = "longitude"
forecast_retry = 5

# Arduino Temp
global arduino_ip_addr, arduino_port, arduino_tmo, arduino_retry
arduino_ip_addr = "ip addr"
arduino_port = 80
arduino_tmo = 5
arduino_retry = 5

# MySQL
global mysql_host, mysql_login, mysql_pw, mysql_db
mysql_host = 'localhost'
mysql_login = 'root'
mysql_pw = 'root'
mysql_db = 'home_automation'
mysql_table = 'sensordata'

# TempoDB keys
#global tempo_key, tempo_secret
#tempo_key = "91a98a060ee543f0911a4c348adb9b92"
#tempo_secret = "11d549fc1bca45ff8ede1447920c6212"

# Plotly credentials
global plotly_un, plotly_key
plotly_un = 'user name'
plotly_key = 'key'

