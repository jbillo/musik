from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import String, Integer

import os, os.path

# Loosely wraps the SQLAlchemy database types and access methods.
# The goal here isn't to encapsulate SQLAlchemy. Rather, we want to
# dictate the process of connecting to and disconnecting from the db,
# as well as the data types that the application uses once connected.
class DB:
	# Helper to map and register a Python class a db table
	Base = declarative_base()

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


	# constructs the database path, creates a database engine
	# and initializes the database if necessary.
	def __init__(self):
		db_path = os.path.abspath(os.path.join(os.curdir, 'musik.db'))
		self.sa_engine = create_engine('sqlite:///%s' % db_path, echo=True)
		self.Base.metadata.create_all(self.sa_engine)

	# returns an initialized instance of sqlalchemy.engine.base.Engine
	def getEngine(self):
		return self.sa_engine