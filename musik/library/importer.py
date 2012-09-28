from datetime import datetime
import mimetypes
import os
import threading
import time

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from musik import initLogging
from musik.db import DatabaseWrapper, ImportTask, Track, Album
from musik.util import EasygoingDictionary

class ImportThread(threading.Thread):

	running = True		# whether or not the thread should continue to run
	sa_session = None	# database session
	log = None			# logging instance

	def __init__(self):
		"""Creates a new instance of ImportThread and connects to the database.
		This design pattern is important: since the constructor runs synchonously,
		it ensures that two threads don't attempt to initialize the database at
		the same time.
		"""
		super(ImportThread, self).__init__(name=__name__)
		self.log = initLogging(__name__)
		db = DatabaseWrapper()
		self.sa_session = db.get_session()

	def run(self):
		"""Checks for new import tasks once per second and passes them off to
		the appropriate handler functions for completion.
		"""
		try:
			# process 'till you drop
			while self.running:

				# find the first unprocessed import task
				task = self.sa_session.query(ImportTask).filter(ImportTask.started == None).order_by(ImportTask.created).first()
				if task != None:
					# start processing it
					task.started = datetime.utcnow()
					self.sa_session.commit()
					self.log.info(u'%s is processing task %s', self.getName(), unicode(task))

					# process the task
					if os.path.isdir(task.uri):
						self.log.info(u'Importing directory %s', task.uri)
						self.importDirectory(task.uri)
					elif os.path.isfile(task.uri):
						self.log.info(u'Importing file %s', task.uri)
						self.importFile(task.uri)
					else:
						self.log.warning(u'Unrecognized URI %s', task.uri)

					task.completed = datetime.utcnow()
					self.sa_session.commit()
					self.log.info(u'%s has finished processing task %s', self.getName(), unicode(task))

				time.sleep(1)

		finally:
			# always clean up - your mom doesn't work here
			if self.sa_session != None:
				self.sa_session.close()
				self.sa_session = None


	# adds a directory to the local library
	# in practice, this is a breadth-first searche over the specified directory and its
	# subdirectories that places appropriate files back into the import queue
	# TODO: directory permissions. Make sure that we can read before we try to
	def importDirectory(self, uri):
		searchQueue = [uri]
		while len(searchQueue) > 0:
			# this is the current working directory
			baseuri = searchQueue.pop(0)
			if os.path.isdir(baseuri) == False:
				continue

			# iterate over the subdirectories and files in the current working directory
			entries = os.listdir(baseuri)
			for subdir in entries:

				# if we found a directory, put it back on the queue. otherwise, process it
				newuri = os.path.join(baseuri, subdir)
				if os.path.isdir(newuri):
					searchQueue.append(newuri)
				elif os.path.isfile(newuri):
					if self.isMimeTypeSupported(newuri):
						# create a new import task for useful files
						newtask = ImportTask(newuri)
						self.sa_session.add(newtask)
						self.sa_session.commit()
					else:
						self.log.debug(u'Ignoring file %s', newuri)


	# returns True if the mime type of the specified uri is supported
	# this should only support audio files
	# TODO: query gstreamer (or whatever other backend we're using) to determine support up front
	def isMimeTypeSupported(self, uri):
		mtype = mimetypes.guess_type(uri)[0]
		if mtype == u'audio/mpeg' or mtype == u'audio/flac' or mtype == u'audio/ogg' or mtype == u'audio/x-wav':
			return True
		else:
			return False


	def importFile(self, uri):
		#TODO: actually import the file
		self.log.info(u'ImportFile called with uri %s', uri)

		mtype = mimetypes.guess_type(uri)[0]
		if mtype == u'audio/mpeg':
			pass
		else:
			self.log.info(u'Unsupported mime type %s. Ignoring file.', mtype)


	def readMp3MetaData(self, uri):
		# get id3 data from the file
		easyid3 = EasyID3(uri)

		# copy data to a new dict that only uses the first value of each key.
		# technically this is discarding data, but most keys are only allowed
		# a single value anyway, and it simplifies the following algorithm
		metadata = EasygoingDictionary()
		for key in easyid3.keys():
			metadata[key] = easyid3[key][0]

		# TODO: handle these keys
		#'album', 'albumartistsort', 'albumsort', 'arranger', 'asin', 'author',
		#'barcode', 'bpm', 'compilation', 'composer', 'composersort',
		#'conductor', 'copyright', 'date', 'discnumber', 'discsubtitle',
		#'encodedby', 'genre', 'isrc', 'length', 'lyricist', 'media', 'mood',
		#'musicbrainz_albumid', 'musicbrainz_albumstatus',
		#'musicbrainz_albumtype', 'musicbrainz_artistid', 'musicbrainz_discid',
		#'musicbrainz_trackid', 'musicbrainz_trmid', 'musicip_fingerprint',
		#'musicip_puid', 'organization', 'performer', 'performer:*',
		#'releasecountry', 'replaygain_*_gain', 'replaygain_*_peak', 'title',
		#'titlesort', 'tracknumber', 'version', 'website'

		track = Track(uri)
		track.artist = self.findArtist(metadata['artist'], metadata['artistsort'], metadata['musicbrainz_artistid'])


	def findArtist(name=None, name_sort=None, musicbrainz_id=None):
		"""Searches the database for an existing artist that matches the specified criteria.
		If no existing artist can be found, a new artist is created with the criteria
		"""
		artist = None
		if musicbrainz_id != None:
			# we trust musicbrainz_artistid the most because it infers that
			# some other tagger has already verified the metadata.
			artist = self.sa_session.query(Artist).filter(Artist.musicbrainz_artistid == musicbrainz_id).first()
			if artist != None:
				# found an existing artist in our db - compare its metadata
				# to the new info. Always prefer existing metadata over new.
				if name != None:
					if artist.name == None:
						artist.name = name
					elif artist.name != name:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Artist name conflict for musicbrainz_artistid %s: %s != %s', artist.musicbrainz_artistid, artist.name, name)
				if name_sort != None:
					if artist.name_sort == None:
						artist.name_sort = name_sort
					elif artist.name_sort != name_sort:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Artist sort name conflict for musicbrainz_artistid %s: %s != %s', artist.musicbrainz_artistid, artist.name_sort, name_sort)

		if artist == None and name != None:
			# if we don't have musicbrainz_artistid or there is no matching
			# artist in our db, try to find an existing artist by name
			artist = self.sa_session.query(Artist).filter(Artist.name == name).first()
			if artist != None:
				# found an existing artist in our db - compare its metadata
				# to the new info. Always prefer existing metadata over new.
				if name_sort != None:
					if artist.name_sort == None:
						artist.name_sort = name_sort
					elif artist.name_sort != name_sort:
						self.log.warning(u'Artist sort name conflict for artist %s: %s != %s', artist.name, artist.name_sort, name_sort)
			else:
				# an existing artist could not be found in our db. Make a new one
				artist = Artist(name)
				if name_sort != None:
					artist.name_sort = name_sort
				if musicbrainz_id != None:
					artist.musicbrainz_artistid = musicbrainz_id

		# return the artist that we found and/or created
		return artist


	# cleans up the thread
	def stop(self):
		self.log.info(u'%s.stop has been called', self.getName())
		self.running = False