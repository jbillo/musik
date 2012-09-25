from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import String, Integer, DateTime

from datetime import datetime
import os, os.path

# Helper to map and register a Python class a db table
Base = declarative_base()

# Represents an import task
class ImportTask(Base):
	__tablename__ = 'import_tasks'
	id = Column(Integer, primary_key=True)
	uri = Column(String)
	created = Column(DateTime)
	started = Column(DateTime)
	completed = Column(DateTime)

	def __init__(self, uri):
		Base.__init__(self)
		self.uri = uri
		self.created = datetime.utcnow()

	def __str__(self):
		return "Import task %s created at %s, started at %s, completed at %s" % (self.uri, str(self.created), str(self.started), str(self.completed))

	@staticmethod
	def list(session):
		return session.query(ImportTask).all()


# Represents a media file on the local hard drive
class Media(Base):
	__tablename__ = 'media'
	id = Column(Integer, primary_key=True)
	uri = Column(String)

	def __init__(self, uri):
		Base.__init__(self)
		self.uri = uri

	def __str__(self):
		return self.uri

	@staticmethod
	def list(session):
		return session.query(Media).all()

# Loosely wraps the SQLAlchemy database types and access methods.
# The goal here isn't to encapsulate SQLAlchemy. Rather, we want to
# dictate the process of connecting to and disconnecting from the db,
# as well as the data types that the application uses once connected.
class DB:

	# constructs the database path, creates a database engine
	# and initializes the database if necessary.
	def __init__(self):
		db_path = os.path.abspath(os.path.join(os.curdir, 'musik.db'))
		self.sa_engine = create_engine('sqlite:///%s' % db_path, echo=True)
		Base.metadata.create_all(self.sa_engine)

	# returns an initialized instance of sqlalchemy.engine.base.Engine
	def getEngine(self):
		return self.sa_engine