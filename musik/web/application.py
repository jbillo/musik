import sys
import os

import cherrypy
from cherrypy.process import wspbus, plugins

from mako.template import Template
from mako.lookup import TemplateLookup

from sqlalchemy.orm import scoped_session, sessionmaker

from musik.db import DatabaseWrapper
from musik.web import api


# Template looker-upper that handles loading and caching of mako templates
templates = TemplateLookup(directories=['templates'], module_directory='templates/compiled')


# A plugin to help SQLAlchemy bind correctly to CherryPy threads
# See http://www.defuze.org/archives/222-integrating-sqlalchemy-into-a-cherrypy-application.html
class SAEnginePlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)
        self.sa_engine = None
        self.bus.subscribe(u'bind', self.bind)

    def start(self):
    	self.db = DatabaseWrapper()
        self.sa_engine = self.db.get_engine()

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

	def _header(self, **kwargs):
		return templates.get_template('header.html').render(**kwargs)

	def _footer(self, **kwargs):
		return templates.get_template('footer.html').render(**kwargs)

	def _render(self, template_name, **kwargs):
		return templates.get_template(template_name).render(**kwargs)

	# Render an entire page with the passed variables
	def _render_page(self, template_names, **kwargs):
		result = []

		if type(template_names) != list:
			# Create one-element list
			template_names = [template_names]

		# Make sure mandatory variables are always in kwargs
		# These will cause the page to fail miserably if not present
		mandatory_vars = ('title', 'js_appends')
		for var in mandatory_vars:
			if var not in kwargs:
				kwargs[var] = u''

		result.append(self._header(**kwargs))

		for template in template_names:
			result.append(self._render(template, **kwargs))

		result.append(self._footer(**kwargs))
		return result

	@cherrypy.expose
	def index(self):
		return self._render_page("index.html", **{
			"title": "Home",
		})

	@cherrypy.expose
	def albums(self):
		return self._render("albums.html")

	@cherrypy.expose
	def artists(self):
		return self._render("artists.html")

	@cherrypy.expose
	def importmedia(self):
		return self._render_page("importmedia.html", **{
			"title": "Import Media",
			"js_appends": ['importmedia/validator.js'],
		})


# starts the web app. this call will block until the server goes down
class MusikWebApplication:
    log = threads = None

    def __init__(self, log, threads):
        self.log = log
        self.threads = threads

        # Subscribe specifically to the 'stop' method passed by cherrypy.
        # This lets us cleanly stop all threads executed by the application.
        SAEnginePlugin(cherrypy.engine).subscribe()
        cherrypy.engine.subscribe("stop", self.stop_threads)
        cherrypy.tools.db = SATool()

        config = {'/':
			{
				'tools.db.on': True,
				'tools.staticdir.root': os.path.dirname(os.path.realpath(sys.argv[0])),
			},
			'/static':
			{
				'tools.staticdir.on': True,
				'tools.staticdir.dir': "static",
			},
		}
        cherrypy.tree.mount(Musik(), '/', config=config)


    # a blocking call that starts the web application listening for requests
    def start(self, port=8080):
        cherrypy.config.update({'server.socket_host': '0.0.0.0',})
        cherrypy.config.update({'server.socket_port': port,})
        cherrypy.engine.start()
        cherrypy.engine.block()

    # stops the web application
    def stop(self):
    	self.log.info(u"Trying to stop main web application")
        cherrypy.engine.stop()

    # stop all threads before closing out this thread
    def stop_threads(self):
        self.log.info(u"Trying to stop all threads")
        for thread in self.threads:
            if thread.is_alive():
                thread.stop()
