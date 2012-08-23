import cherrypy

class Albums:
	def index(self):
		return "A list of all known albums"
	index.exposed = True

	def default(self, album):
		return "Album page for %s" %album
	default.exposed = True


class Artists:
	albums = Albums()
	
	def index(self):
		return "A list of all known artists"
	index.exposed = True

	def default(self, artist):
		return "Artist page for %s" %artist
	default.exposed = True


# defines the restful api that all client applications use
class Api:
	artists = Artists()
	albums = Albums()

	def index(self):
		return "Welcome to the API"
	index.exposed = True


# defines the web application that is the default client
class Musik:
	api = Api()

	def index(self):
		return "Welcome to the Application"
	index.exposed = True

cherrypy.quickstart(Musik())
