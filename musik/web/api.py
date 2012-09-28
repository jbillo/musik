import re

import cherrypy

from musik.db import ImportTask


class Import:
	@cherrypy.expose
	def directory(self, path):
		task = ImportTask(path)
		cherrypy.request.db.add(task)

		#TODO: return JSON instead of text
		return u'Importing %s' % unicode(task.uri)

	@cherrypy.expose
	def status(self):
		# gets the number of outstanding importer tasks
		numtasks = cherrypy.request.db.query(ImportTask).filter(ImportTask.started == None).filter(ImportTask.completed == None).count()

		# get the currently processing task
		currentTask = cherrypy.request.db.query(ImportTask).filter(ImportTask.started != None).filter(ImportTask.completed == None).first()

		ret = u''
		if (currentTask != None):
			ret += u'The importer is currently processing %s.<br />' % unicode(currentTask.uri)

		#TODO: calculate estimated completion time by multiplying average job time by number of outstanding items

		#TODO: return JSON instead of text
		if numtasks == 0:
			ret += u'There are no tasks currently pending'
		else:
			ret += u'There are %d tasks currently pending' % numtasks

		return ret


# defines an api with a dynamic url scheme composed of /<tag>/<value>/ pairs
# these pairs are assembled into an SQL query. Each term is combined with the AND operator.
# unknown <tag> elements are ignored.
class API:
	importmedia = Import()

	@cherrypy.expose
	def default(self, *params):
		#TODO: pull all available tags from the database so this regex is dynamic and allows any tag
		regex = re.compile('genre|artist|album|track')

		#TODO: instead of a string, assemble an SQL query
		str = u''
		for index in xrange(0, len(params), 2):
			if regex.match(params[index]):
				str += params[index] + u': '

				if len(params) > (index + 1):
					str += params[index + 1] + u'<br />'
				else:
			 		str += u'* <br />'
	 		else:
	 			str = u'Invalid Query'
	 			break

		return str
