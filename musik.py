from musik.db import DB

from multiprocessing import Process
import re
import time
from threading import Lock

import cherrypy
from cherrypy.process import wspbus, plugins

from mako.template import Template
from mako.lookup import TemplateLookup

from sqlalchemy.orm import scoped_session, sessionmaker

# Template looker-upper that handles loading and caching of mako templates
templates = TemplateLookup(directories=['templates'], module_directory='templates/compiled')

 # A plugin to help SQLAlchemy bind correctly to CherryPy threads
 # See http://www.defuze.org/archives/222-integrating-sqlalchemy-into-a-cherrypy-application.html
class SAEnginePlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)
        self.sa_engine = None
        self.bus.subscribe("bind", self.bind)

    def start(self):
    	self.db = DB()
        self.sa_engine = self.db.getEngine()

    def stop(self):
        if self.sa_engine:
            self.sa_engine.dispose()
            self.sa_engine = None

    def bind(self, session):
        session.configure(bind=self.sa_engine)

# A tool to help SQLAlchemy correctly dole out and clean up db connections
# See http://www.defuze.org/archives/222-integrating-sqlalchemy-into-a-cherrypy-application.html
class SATool(cherrypy.Tool):
    def __init__(self):
        cherrypy.Tool.__init__(self, 'on_start_resource', self.bind_session, priority=20)
        self.session = scoped_session(sessionmaker(autoflush=True, autocommit=False))

    def _setup(self):
        cherrypy.Tool._setup(self)
        cherrypy.request.hooks.attach('on_end_resource', self.commit_transaction, priority=80)

    def bind_session(self):
        cherrypy.engine.publish('bind', self.session)
        cherrypy.request.db = self.session

    def commit_transaction(self):
        cherrypy.request.db = None
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.remove()


# provides functionality for adding new media to the database
# TODO: There's a scoping issue somewhere in here. processimports() seems to run and update totalItems, but status() can't see the updates
class Import:

	# a worker thread responsible for importing media into the application
	importmedia_process = None

	totalItems = 0
	currentItem = 0
	itemLock = Lock()

	@cherrypy.expose
	def directory(self, path):

		#TODO: enumerate the directory at path into a list of files
		#TODO: for each file - if file mime type is valid, add it to database import table
		#TODO: ensure that importmedia_process thread is started - it will process the import table

		if self.importmedia_process is None:
			self.importmedia_process = Process(target=self.processimports)
			self.importmedia_process.start()

		return "Importing the directory %s" % path

	@cherrypy.expose
	def status(self):
		#TODO: this method should return the status of the importer, including file currently being processed, and completion % of import job
		if self.importmedia_process is None or self.importmedia_process.is_alive()==False:
			return "Nothing is being imported at this time."
		else:
			with self.itemLock:
				cherrypy.log(str(self.currentItem))
				return "Currently processing item %s of %s" % (self.currentItem, self.totalItems)

	def processimports(self):
		#TODO: pull all files to be processed from the database import table
		#TODO: foreach file - actually add it to the database correctly and delete it from the import table
		with self.itemLock:
			self.totalItems = 100
			self.currentItem = 0

		for x in range(0, 100):
			with self.itemLock:
				self.currentItem += 1
				cherrypy.log("Current Item is %s" % str(self.currentItem))
			time.sleep(1)

		self.importmedia_process = None
		return None


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

		return str


# defines the web application that is the default client
class Musik:
	api = API()

	@cherrypy.expose
	def index(self):
		return templates.get_template('index.html').render()

	@cherrypy.expose
	def importmedia(self):
		return templates.get_template('importmedia.html').render()


# application entry - starts the database connection and dev server
if __name__ == '__main__':
    SAEnginePlugin(cherrypy.engine).subscribe()
    cherrypy.tools.db = SATool()
    cherrypy.tree.mount(Musik(), '/', {'/': {'tools.db.on': True}})
    cherrypy.engine.start()
    cherrypy.engine.block()