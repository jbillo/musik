import cherrypy
import re

# defines an api with a dynamic url scheme composed of /<tag>/<value>/ pairs
# these pairs are assembled into an SQL query. Each term is combined with the AND operator.
# unknown <tag> elements are ignored.
class API:

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

		return str
	default.exposed = True

# defines the web application that is the default client
class Musik:
	api = API()

	def index(self):
		return "Welcome to the Application"
	index.exposed = True

cherrypy.quickstart(Musik())
