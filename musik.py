import musik.web.application
import musik.library.importer
import signal

app = None
importThread = None

# cleans up and safely stops the application
def cleanup(signum=None, frame=None):
	if type(signum) == type(None):
		pass
	else:
		print "Signal %i caught, saving and exiting..." % int(signum)

	print "Stopping worker threads"
	if importThread != None:
		importThread.stop()
		importThread.join(5)
		if importThread.isAlive():
			print "Failed to clean up importThread"

	print "Stopping CherryPy Engine"
	app.stop()

	print "Clean up complete"


# application entry - starts the database connection and dev server
if __name__ == '__main__':
	#TODO: also register for CherryPy shutdown messages
	print "Registering for shutdown signals"
	signal.signal(signal.SIGINT, cleanup)
	signal.signal(signal.SIGTERM, cleanup)

	print "Starting worker threads"
	importThread = musik.library.importer.ImportThread(name="ImportThread")
	importThread.start()

	# this is a blocking call
	print "Starting Web App"
	app = musik.web.application.MusikWebApplication()
	app.start()