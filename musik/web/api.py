import cherrypy
import re

from musik.db import ImportTask

class Import:
	@cherrypy.expose
	def directory(self, path):
		task = ImportTask(path)
		cherrypy.request.db.add(task)

		#TODO: return JSON instead of text
		return "Created the import task %s" % str(task)

	@cherrypy.expose
	def status(self):
		# gets the number of outstanding importer tasks
		numtasks = cherrypy.request.db.query(ImportTask).filter(ImportTask.started == None).filter(ImportTask.completed == None).count()

		# get the currently processing task
		currentTask = cherrypy.request.db.query(ImportTask).filter(ImportTask.started != None).filter(ImportTask.completed == None).first()

		ret = ""
		if (currentTask != None):
			ret += "The importer is currently processing %s.<br />" % str(currentTask)

		#TODO: calculate estimated completion time by multiplying average job time by number of outstanding items

		#TODO: return JSON instead of text
		if numtasks == 0:
			ret += "There are no tasks currently pending"
		else:
			ret += "There are %d tasks currently pending" % numtasks

		return ret


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
