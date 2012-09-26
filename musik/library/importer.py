import threading
import time

class ImportThread(threading.Thread):

	running = True

	def run(self):
		while self.running:
			print "still here"
			time.sleep(1)

	def stop(self):
		print "%s.stop has been called" % self.getName()
		self.running = False