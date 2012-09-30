from datetime import datetime
import mimetypes
import os
import threading
import time

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from musik import initLogging
from musik.db import DatabaseWrapper, ImportTask, Track, Album, Artist
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
				try:
					task = self.sa_session.query(ImportTask).filter(ImportTask.started == None).order_by(ImportTask.created).first()
				except ex as OperationalError:
					# Ran into this when my SQLite database was locked. 
					self.log.error(u'Operational error accessing database. Ensure it is not open by another process.')
					break
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
		if mtype != u'audio/mpeg':
			self.log.info(u'Unsupported mime type %s. Ignoring file.', mtype)

		# Try to read the metadata appropriately.
		metadata = self.readMp3MetaData(uri)


	def readMp3MetaData(self, uri):
		# TODO: check that the uri doesn't already exist

		# get id3 data from the file
		easyid3 = EasyID3(uri)

		# copy data to a new dict that only uses the first value of each key.
		# technically this is discarding data, but most keys are only allowed
		# a single value anyway, and it simplifies the following algorithm
		metadata = EasygoingDictionary()
		for key in easyid3.keys():
			metadata[key] = easyid3[key][0]

		# TODO: handle these keys
		# 'asin', 'author', 'bpm', 'copyright', 'date',
		# 'encodedby', 'genre', 'isrc', 'length', 'mood',
		# 'musicbrainz_trackid', 'musicbrainz_trmid',
		# 'musicip_fingerprint', 'musicip_puid', 'performer:*',
		# 'replaygain_*_gain', 'replaygain_*_peak', 'title', 'titlesort',
		# 'tracknumber', 'version', 'website'

		track = Track(uri)
		track.artist = self.findArtist(metadata['artist'], metadata['artistsort'], metadata['musicbrainz_artistid'])
		track.album_artist = self.findArtist(metadata['albumartist'], metadata['albumartistsort'])
		track.arranger = self.findArtist(metadata['arranger'])
		track.composer = self.findArtist(metadata['composer'], metadata['composersort'])
		track.conductor = self.findArtist(metadata['conductor'])
		track.lyricist = self.findArtist(metadata['lyricist'])
		track.performer = self.findArtist(metadata['performer'])
		track.title = metadata['title']

		track.album = self.findAlbum(metadata['album'], metadata['albumsort'], metadata['musicbrainz_albumid'])
		if track.album != None:
			disc = self.findDisc(track.album, metadata['discnumber'], metadata['discsubtitle'], metadata['musicbrainz_discid'])
			
		return track


	def findArtist(self, name=None, name_sort=None, musicbrainz_id=None):
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
				self.log.debug(u'Found existing artist %s in database' % name)
				# found an existing artist in our db - compare its metadata
				# to the new info. Always prefer existing metadata over new.
				if name_sort != None:
					if artist.name_sort == None:
						artist.name_sort = name_sort
					elif artist.name_sort != name_sort:
						self.log.warning(u'Artist sort name conflict for artist %s: %s != %s', artist.name, artist.name_sort, name_sort)
			else:
				# an existing artist could not be found in our db. Make a new one
				self.log.debug(u'Artist not found in database; creating %s' % name)
				artist = Artist(name)
				if name_sort != None:
					artist.name_sort = name_sort
				if musicbrainz_id != None:
					artist.musicbrainz_artistid = musicbrainz_id
				# add the artist object to the DB 
				self.sa_session.add(artist)

		# return the artist that we found and/or created
		return artist


	def findAlbum(self, title=None, title_sort=None, musicbrainz_id=None, artist=None, metadata=None):
		"""Searches the database for an existing album that matches the specified criteria.
		If no existing album can be found, a new album is created with the criteria.
		"""
		album = None
		if musicbrainz_id != None:
			# we trust musicbrainz_albumid the most because it infers that
			# some other tagger has already verified the metadata.
			album = self.sa_session.query(Album).filter(Album.musicbrainz_albumid == musicbrainz_id).first()
			if album != None:
				# found an existing album in our db - compare its metadata
				# to the new info. Always prefer existing metadata over new.
				if title != None:
					if album.title == None:
						album.title = title
					elif album.title != title:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Album title conflict for musicbrainz_albumid %s: %s != %s', album.musicbrainz_albumid, album.title, title)
				if title_sort != None:
					if album.title_sort == None:
						album.title_sort = title_sort
					elif album.title_sort != title_sort:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Album sort title conflict for musicbrainz_albumid %s: %s != %s', album.musicbrainz_albumid, album.title_sort, title_sort)
				if artist != None:
					if album.artist == None:
						album.artist = artist
					elif album.artist.id != artist.id:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Album artist conflict for musicbrainz_albumid %s: %s != %s', album.musicbrainz_albumid, album.artist, artist)

		if album == None and title != None and artist != None:
			# if we don't have musicbrainz_albumid or there is no matching
			# album in our db, try to find an existing album by title and artist
			album = self.sa_session.query(Album).filter(Album.title == title, Album.artist.id == artist.id).first()
			if album != None:
				# found an existing album in our db - compare its metadata
				# to the new info. Always prefer existing metadata over new.
				self.log.debug(u'Found existing album %s in database' % title)
				if title_sort != None:
					if album.title_sort == None:
						album.title_sort = title_sort
					elif album.title_sort != title_sort:
						self.log.warning(u'Album sort title conflict for album %s: %s != %s', album.title, album.title_sort, title_sort)
			else:
				# an existing album could not be found in our db. Make a new one
				self.log.debug(u'Album not found in database; creating %s' % title)
				album = Album(title)
				if title_sort != None:
					album.title_sort = title_sort
				if musicbrainz_id != None:
					album.musicbrainz_albumid = musicbrainz_id
				if artist != None:
					album.artist = artist
				self.sa_session.add(album)

		# we either found or created the album. now verify its metadata
		if album != None and metadata != None:
			if metadata['barcode'] != None:
				if album.barcode == None:
					album.barcode = metadata['barcode']
				elif album.barcode != metadata['barcode']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album barcode conflict for album %s: %s != %s', album, album.barcode, metadata['barcode'])
			if metadata['compilation'] != None:
				if album.compilation == None:
					album.compilation = metadata['compilation']
				elif album.compilation != metadata['compilation']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album compilation conflict for album %s: %s != %s', album, album.compilation, metadata['compilation'])
			if metadata['media'] != None:
				if album.media_type == None:
					album.media_type = metadata['media']
				if album.media_type != metadata['media']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album media type conflict for album %s: %s != %s', album, album.media_type, metadata['media'])
			if metadata['musicbrainz_albumstatus'] != None:
				if album.musicbrainz_albumstatus == None:
					album.musicbrainz_albumstatus = metadata['musicbrainz_albumstatus']
				elif album.musicbrainz_albumstatus != metadata['musicbrainz_albumstatus']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album musicbrainz_albumstatus conflict for album %s: %s != %s', album, album.musicbrainz_albumstatus, metadata['musicbrainz_albumstatus'])
			if metadata['musicbrainz_albumtype'] != None:
				if album.musicbrainz_albumtype == None:
					album.musicbrainz_albumtype = metadata['musicbrainz_albumtype']
				elif album.musicbrainz_albumtype != metadata['musicbrainz_albumtype']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album musicbrainz_albumtype conflict for album %s: %s != %s', album, album.musicbrainz_albumtype, metadata['musicbrainz_albumtype'])
			if metadata['organization'] != None:
				if album.organization == None:
					album.organization = metadata['organization']
				elif album.organization != metadata['organization']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album organization conflict for album %s: %s != %s', album, album.organization, metadata['organization'])
			if metadata['releasecountry'] != None:
				if album.releasecountry == None:
					album.releasecountry = metadata['releasecountry']
				elif album.releasecountry != metadata['releasecountry']:
					# TODO: conflict -> schedule musicbrainz task!
					self.log.warning(u'Album release country conflict for album %s: %s != %s', album, album.releasecountry, metadata['releasecountry'])

		return album


	def findDisc(self, album=None, discnumber=None, discsubtitle=None, musicbrainz_id=None):
		"""Tries to find an existing disc that matches the specified criteria.
		If an existing disc cannot be found, creates a new disc with the specified criteria.
		"""
		# TODO: first, see if there's a disc that's already linked that satisfies the specified criteria
		# if album != None:
		# 	for disc in album.discs:
		# 		if musicbrainz_id != None:
		# 			if disc.musicbrainz_id == musicbrainz_id:
		# 				if discnumber != None:
		# 					if disc.discnumber == None:
		# 						disc.discnumber = discnumber
		# 					elif

		disc = None
		if musicbrainz_id != None:
			# we trust musicbrainz_discid the most because it infers that
			# some other tagger has already verified the metadata.
			disc = self.sa_session.query(Disc).filter(Disc.musicbrainz_discid == musicbrainz_id).first()
			if disc != None:
				if album != None:
					if disc.album == None:
						disc.album = album
					elif disc.album.id != album.id:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Disc album conflict for disc %s: %s != %s', disc, disc.album, album)
				if discnumber != None:
					if disc.discnumber == None:
						disc.discnumber = discnumber
					elif disc.discnumber != discnumber:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Disc number conflict for disc %s: %s != %s', disc, disc.discnumber, discnumber)
				if discsubtitle != None:
					if disc.discsubtitle == None:
						disc.discsubtitle = discsubtitle
					elif disc.discsubtitle != discsubtitle:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Disc subtitle conflict for disc %s: %s != %s', disc, disc.discsubtitle, discsubtitle)
		if album != None and discnumber != None:
			# musicbrainz_discid wasn't supplied or didn't yield an existing album.
			# try to search with album id and disc number instead.
			disc = self.sa_session.query(Disc).filter(Disc.album_id == album.id, Disc.discnumber == discnumber)
			if disc != None:
				if discsubtitle != None:
					if disc.discsubtitle == None:
						disc.discsubtitle = discsubtitle
					elif disc.discsubtitle != discsubtitle:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Disc subtitle conflict for disc %s: %s != %s', disc, disc.discsubtitle, discsubtitle)
				if musicbrainz_id != None:
					if disc.musicbrainz_discid == None:
						disc.musicbrainz_discid = musicbrainz_id
					elif disc.musicbrainz_discid != musicbrainz_id:
						# TODO: conflict -> schedule musicbrainz task!
						self.log.warning(u'Disc musicbrainz_discid conflict for disc %s: %s != %s', disc, disc.musicbrainz_discid, musicbrainz_id)
			else:
				# could not find the disc in question. Create a new one instead
				self.log.debug(u'Could not find disc in database; creating %s' % discnumber)				
				disc = Disc(discnumber)
				if album != None:
					disc.album = album
				if discsubtitle != None:
					disc.discsubtitle = discsubtitle
				if musicbrainz_id != None:
					disc.musicbrainz_discid = musicbrainz_id
				self.sa_session.add(disc)

		return disc


	def stop(self):
		"""Cleans up the thread"""
		self.log.info(u'%s.stop has been called', self.getName())
		self.running = False
