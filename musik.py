
import musik.web.application

from multiprocessing import Process
import time
from threading import Lock

# provides functionality for adding new media to the database
# TODO: There's a scoping issue somewhere in here. processimports() seems to run and update totalItems, but status() can't see the updates
# class Import:

# 	# a worker thread responsible for importing media into the application
# 	importmedia_process = None

# 	totalItems = 0
# 	currentItem = 0
# 	itemLock = Lock()

# 	@cherrypy.expose
# 	def directory(self, path):

# 		#TODO: enumerate the directory at path into a list of files
# 		#TODO: for each file - if file mime type is valid, add it to database import table
# 		#TODO: ensure that importmedia_process thread is started - it will process the import table

# 		if self.importmedia_process is None:
# 			self.importmedia_process = Process(target=self.processimports)
# 			self.importmedia_process.start()

# 		return "Importing the directory %s" % path

# 	@cherrypy.expose
# 	def status(self):
# 		#TODO: this method should return the status of the importer, including file currently being processed, and completion % of import job
# 		if self.importmedia_process is None or self.importmedia_process.is_alive()==False:
# 			return "Nothing is being imported at this time."
# 		else:
# 			with self.itemLock:
# 				cherrypy.log(str(self.currentItem))
# 				return "Currently processing item %s of %s" % (self.currentItem, self.totalItems)

# 	def processimports(self):
# 		#TODO: pull all files to be processed from the database import table
# 		#TODO: foreach file - actually add it to the database correctly and delete it from the import table
# 		with self.itemLock:
# 			self.totalItems = 100
# 			self.currentItem = 0

# 		for x in range(0, 100):
# 			with self.itemLock:
# 				self.currentItem += 1
# 				cherrypy.log("Current Item is %s" % str(self.currentItem))
# 			time.sleep(1)

# 		self.importmedia_process = None
# 		return None


# application entry - starts the database connection and dev server
if __name__ == '__main__':
	self.app = musik.web.application.MusikWebApplication()