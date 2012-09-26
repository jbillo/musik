from musik.db import DB
from musik.web import api

import cherrypy
from cherrypy.process import wspbus, plugins

from sqlalchemy.orm import scoped_session, sessionmaker

from mako.template import Template
from mako.lookup import TemplateLookup

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

# defines the web application that is the default client
class Musik:
	api = api.API()

	@cherrypy.expose
	def index(self):
		return templates.get_template('index.html').render()

	@cherrypy.expose
	def importmedia(self):
		return templates.get_template('importmedia.html').render()


# starts the web app. this call will block until the server goes down
class MusikWebApplication:
    def __init__(self):
        SAEnginePlugin(cherrypy.engine).subscribe()
        cherrypy.tools.db = SATool()
        cherrypy.tree.mount(Musik(), '/', {'/': {'tools.db.on': True}})
        cherrypy.engine.start()
        cherrypy.engine.block()