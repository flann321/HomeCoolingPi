1. Setup Accounts

	Plotly
	a. Create account at http://plot.ly
	b. Generate API Key on website
	c. Enter user name and API key in python script Credential.py

	Nest
	a. Create nest account
	b. Link Nest thermostat
	
	Forecast.IO
	
	Wemo
	a. Setup Wemo switch with Wemo app	

2. Set timezone to PST permanently by adding to /home/pi/.profile
	echo "TZ='America/Los_Angeles'; export TZ" >.profile
	sudo raspi-config
	Select Internationalisation Options->Change Timezone

3. 	Enable I2C interface
	sudo raspi-config
	Select Advanced Options->I2C and enable I2C interface and load I2C kernel module

4. Install libraries
	sudo apt-get update
	sudo apt-get install python-pip python-dev mysql-server libmysqlclient-dev samba samba-common-bin git build-essential i2c-tools python-smbus
	sudo pip install plotly MySQL-python
	sudo easy_install ouimeaux

	git clone https://github.com/adafruit/Adafruit_Python_BMP.git
	cd Adafruit_Python_BMP
	sudo python setup.py install

5. 	Setup Samba
	Add user pi
	sudo smbpasswd -a pi

	Edit samba config file
	sudo nano /etc/samba/smb.conf
	
	Uncomment these lines:
	security = user
	socket options = TCP_NODELAY

	Update these lines:
	[homes]
		comment = Home Directories
		browseable = no
		read only = no

	Check for errors in config file
	testparm		

	Restart samba server
	sudo /etc/init.d/samba restart

6. Setup BMP180 pressure sensor
	Append to file:
	sudo nano /etc/modules
	i2c-bcm2708
	i2c-dev

	git clone https://github.com/adafruit/Adafruit_Python_BMP.git
	cd Adafruit_Python_BMP
	sudo python setup.py install


7. Setup MySQL
	Run command:
	mysql_secure_installation
	
	Create database
	mysql -u root -p
	create database home_automation;
	
8. Run python script at startup
	a. Create startup script
	nano ~/startup.sh
	sudo python /home/pi/HomeWeather/HomeWeather.py &
	b. Add line to /etc/rc.local before exit 0
	sudo sh /home/pi/startup.sh
