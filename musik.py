import os, os.path
import re
 
import cherrypy
from cherrypy.process import wspbus, plugins

from mako.template import Template
from mako.lookup import TemplateLookup
 
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import String, Integer
 
# Helper to map and register a Python class a db table
Base = declarative_base()

# Template looker-upper that handles loading and caching of mako templates
templates = TemplateLookup(directories=['templates'], module_directory='templates/compiled')

# Represents a media file on the local hard drive
class Media(Base):
	__tablename__ = 'media'
	id = Column(Integer, primary_key=True)
	path = Column(String)

	def __init__(self, path):
		Base.__init__(self)
		self.path = path

	def __str__(self):
		return self.path.encode('utf-8')

	def __unicode__(self):
		return self.path

	@staticmethod
	def list(session):
		return session.query(Media).all()


#TODO: create an object to represent tags for media objects

 
 # A plugin to help SQLAlchemy bind correctly to CherryPy threads
 # See http://www.defuze.org/archives/222-integrating-sqlalchemy-into-a-cherrypy-application.html
class SAEnginePlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)
        self.sa_engine = None
        self.bus.subscribe("bind", self.bind)
 
    def start(self):
        db_path = os.path.abspath(os.path.join(os.curdir, 'musik.db'))
        self.sa_engine = create_engine('sqlite:///%s' % db_path, echo=True)
        Base.metadata.create_all(self.sa_engine)
 
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
class Import:

	@cherrypy.expose
	def directory(self, path):
		return "Importing the directory %s" % path

	@cherrypy.expose
	def file(self, path):
		return "Importing the file %s" % path


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