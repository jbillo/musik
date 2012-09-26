import musik.db
from musik.db import ImportTask

from datetime import datetime
import threading
import time

class ImportThread(threading.Thread):

	# whether or not the thread should continue to run
	running = True

	# database session
	sa_session = None

	def run(self):
		try:
			# get a database connection
			db = musik.db.DB()
			self.sa_session = db.getSession()

			# process 'till you drop
			while self.running:

				# find the first unprocessed import task
				task = self.sa_session.query(ImportTask).filter(ImportTask.started == None).order_by(ImportTask.created).first()
				if task != None:
					# start processing it
					task.started = datetime.utcnow()
					self.sa_session.commit()
					print "%s is processing task %s" % (self.getName(), str(task))

					# TODO: process the task

					task.completed = datetime.utcnow()
					self.sa_session.commit()
					print "%s has finished processing task %s" % (self.getName(), str(task))

				time.sleep(1)

		finally:
			# always clean up - your mom doesn't work here
			self.sa_session.close()
			self.sa_session = None


	# cleans up the thread
	def stop(self):
		print "%s.stop has been called" % self.getName()
		self.running = False