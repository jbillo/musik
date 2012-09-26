import musik.db
from musik.db import ImportTask

from datetime import datetime
import mimetypes
import os
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
					if os.path.isdir(task.uri):
						print "Importing directory %s" % task.uri
						self.importDirectory(task.uri)
					elif os.path.isfile(task.uri):
						print "Importing file %s" % task.uri
						self.importFile(task.uri)
					else:
						print "ERROR: Unrecognized URI %s" % task.uri

					task.completed = datetime.utcnow()
					self.sa_session.commit()
					print "%s has finished processing task %s" % (self.getName(), str(task))

				time.sleep(1)

		finally:
			# always clean up - your mom doesn't work here
			self.sa_session.close()
			self.sa_session = None


	# adds a directory to the local library
	# in practice, this is a breadth-first searche over the specified directory and its
	# subdirectories that places appropriate files back into the import queue
	# TODO: directory permissions. Make sure that we can read before we try to
	def importDirectory(self, uri):
		searchQueue = [uri]
		while len(searchQueue) > 0:
			# this is the current working directory
			baseuri = searchQueue.pop(0)
			if os.path.isdir(baseuri) == False:
				continue

			# iterate over the subdirectories and files in the current working directory
			entries = os.listdir(baseuri)
			for subdir in entries:

				# if we found a directory, put it back on the queue. otherwise, process it
				newuri = os.path.join(baseuri, subdir)
				if os.path.isdir(newuri):
					searchQueue.append(newuri)
				elif os.path.isfile(newuri):
					if self.isMimeTypeSupported(newuri):
						# create a new import task for useful files
						newtask = ImportTask(newuri)
						self.sa_session.add(newtask)
						self.sa_session.commit()
					else:
						print "ImportThread: ignoring file %s" % newuri


	# returns True if the mime type of the specified uri is supported
	# this should only support audio files
	# TODO: query gstreamer (or whatever other backend we're using) to determine support up front
	def isMimeTypeSupported(self, uri):
		mtype = mimetypes.guess_type(uri)[0]
		if mtype == "audio/mpeg" or mtype == "audio/flac" or mtype == "audio/ogg" or mtype == "audio/x-wav":
			return True
		else:
			return False


	def importFile(self, uri):
		#TODO: (global) logging needs to default to unicode. need a logging class that writes to file anyway
		#TODO: actually import the file
		print "importFile called with uri %s" % uri


	# cleans up the thread
	def stop(self):
		print "%s.stop has been called" % self.getName()
		self.running = False