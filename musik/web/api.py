import cherrypy
import re

class Import:
	@cherrypy.expose
	def directory(self, path):

		#TODO: enumerate the directory at path into a list of files
		#TODO: for each file - if file mime type is valid, add it to database import table
		#TODO: ensure that importmedia_process thread is started - it will process the import table

		# if self.importmedia_process is None:
		# 	self.importmedia_process = Process(target=self.processimports)
		# 	self.importmedia_process.start()

		return "Importing the directory %s" % path

	@cherrypy.expose
	def status(self):
		#TODO: this method should return the status of the importer, including file currently being processed, and completion % of import job
		# if self.importmedia_process is None or self.importmedia_process.is_alive()==False:
			return "Nothing is being imported at this time."
		# else:
		# 	with self.itemLock:
		# 		cherrypy.log(str(self.currentItem))
		# 		return "Currently processing item %s of %s" % (self.currentItem, self.totalItems)

# defines an api with a dynamic url scheme composed of /<tag>/<value>/ pairs
# these pairs are assembled into an SQL query. Each term is combined with the AND operator.
# unknown <tag> elements are ignored.
class API:
	importmedia = Import()

	@cherrypy.expose
	def default(self, *params):
		#TODO: pull all available tags from the database so this regex is dynamic and allows any tag
		regex = re.compile("genre|artist|album|track")

		#TODO: instead of a string, assemble an SQL query
		str = ""
		for index in xrange(0, len(params), 2):
			if regex.match(params[index]):
				str += params[index] + ": "

				if len(params) > (index + 1):
					str += params[index + 1] + "<br />"
				else:
			 		str += "* <br />"
	 		else:
	 			str = "Invalid Query"
	 			break

		return str
