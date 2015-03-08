import time
from ouimeaux.environment import Environment
from ouimeaux.signals import statechange, receiver
import gevent
from gevent.queue import Queue

def main():
	print "Wemo switch toggle test"

	(env, switch) = init('Whole House Fan')
	if switch == None:
		return

	qIn = Queue()

	print "Starting loop..."
	gevent.joinall([
		gevent.spawn(mainloop, env, switch, qIn),
		gevent.spawn(monitorstate, env, switch),
		])

def mainloop(env, switch, qIn):

	print "Starting toggle switch loop..."
	env.wait()  # Pass control to the event loop

	while 1:
		print 'switch on'
		switch.on()
		gevent.sleep(60)

		print 'switch off'
		switch.off()
		gevent.sleep(60)
	


# Create handle to device
# Input device name string
# Return device handle or None if not found
def init(devname):
	try:
		env = Environment()
		env.start()
		env.discover(seconds=3)
		switch = env.get_switch(devname)

	#except UnknownDevice:
	#	return None, None
	except:
		raise

	return env, switch

# Return list of Wemo switches
def devices():
	try:
		env = Environment()
		env.start()
		env.discover(seconds=3)
		result = env.list_switches()
	
	except:
		raise
	
	return result

def on(switch):
	switch.on()
	
def off(switch):
	switch.off()

def monitorstate(env, switch):

	@receiver(statechange, sender=switch)
	def switch_toggle(sender, **kwargs):
		print "%s changed to %s" % (sender.name, kwargs['state'])

	env.wait()  # Pass control to the event loop
	

if __name__ == '__main__':
	main()