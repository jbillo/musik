import json
import re
import os

import cherrypy

from musik.db import Album, Artist, ImportTask, Track


class Import:
	@cherrypy.expose
	def directory(self, path):
		if not path or not os.path.isdir(path):
			raise IOError(u"Path '%s' not found on filesystem" % path)

		task = ImportTask(path)
		cherrypy.request.db.add(task)

		#TODO: return JSON instead of text
		return u'Importing %s' % unicode(task.uri)

	@cherrypy.expose
	def status(self):
		# gets the number of outstanding importer tasks
		numtasks = cherrypy.request.db.query(ImportTask).filter(ImportTask.started == None).filter(ImportTask.completed == None).count()

		# get the currently processing task
		currentTask = cherrypy.request.db.query(ImportTask).filter(ImportTask.started != None).filter(ImportTask.completed == None).first()

		ret = u''
		if (currentTask != None):
			ret += u'The importer is currently processing %s.<br />' % unicode(currentTask.uri)

		#TODO: calculate estimated completion time by multiplying average job time by number of outstanding items

		#TODO: return JSON instead of text
		if numtasks == 0:
			ret += u'There are no tasks currently pending'
		else:
			ret += u'There are %d tasks currently pending' % numtasks

		return ret


# defines an api with a dynamic url scheme composed of /<tag>/<value>/ pairs
# these pairs are assembled into an SQL query. Each term is combined with the AND operator.
# unknown <tag> elements are ignored.
class API:
	importmedia = Import()

	@cherrypy.expose
	def default(self, *params):
		#TODO: pull all available tags from the database so this regex is dynamic and allows any tag
		regex = re.compile('genre|artist|album|track')

		#TODO: instead of a string, assemble an SQL query
		str = u''
		for index in xrange(0, len(params), 2):
			if regex.match(params[index]):
				str += params[index] + u': '

				if len(params) > (index + 1):
					str += params[index + 1] + u'<br />'
				else:
			 		str += u'* <br />'
	 		else:
	 			str = u'Invalid Query'
	 			break

		return str


	@cherrypy.expose
	def artists(self, filter=None):
		"""Returns unique artists in our database, ordered by name_sort property.
		If an integer filter is supplied, it must be the id of an artist. If a string
		filter is supplied, it must be a substring of the name of an artist.
		"""
		cherrypy.response.headers['Content-Type'] = 'application/json'

		artists = []
		if filter != None:
			try:
				artists.extend(cherrypy.request.db.query(Artist).filter(Artist.id == filter).order_by(Artist.name_sort, Artist.name).all())
			except:
				pass

			# only attempt a name match if the id match failed - this prevents 12 from returning D12
			if len(artists) == 0:
				try:
					artists.extend(cherrypy.request.db.query(Artist).filter(Artist.name.like('%' + filter + '%')).order_by(Artist.name_sort, Artist.name).all())
				except:
					pass
		else:
			artists.extend(cherrypy.request.db.query(Artist).order_by(Artist.name_sort, Artist.name).all())

		artist_list = []
		for a in artists:
			artist_list.append(a.as_dict())
		return json.dumps(artist_list)


	@cherrypy.expose
	def albums(self, filter=None):
		"""Returns unique albums in our database, ordered by title_sort property.
		If an integer filter is supplied, it must be the id of an album. If a string
		filter is supplied, it must be a substring of the name of an album.
		"""
		cherrypy.response.headers['Content-Type'] = 'application/json'

		albums = []
		if filter != None:
			try:
				albums.extend(cherrypy.request.db.query(Album).filter(Album.id == filter).order_by(Album.title_sort, Album.title).all())
			except:
				pass

			# only attempt a name match if the id match failed - this prevents 12 from returning D12
			if len(albums) == 0:
				try:
					albums.extend(cherrypy.request.db.query(Album).filter(Album.title.like('%' + filter + '%')).order_by(Album.title_sort, Album.title).all())
				except:
					pass
		else:
			albums.extend(cherrypy.request.db.query(Album).order_by(Album.title_sort, Album.title).all())

		album_list = []
		for a in albums:
			album_list.append(a.as_dict())
		return json.dumps(album_list)


	@cherrypy.expose
	def tracks(self, filter=None):
		"""Returns unique tracks in our database, ordered by title_sort property.
		If an integer filter is supplied, it must be the id of a track. If a string
		filter is supplied, it must be a substring of the title of a track.
		"""
		cherrypy.response.headers['Content-Type'] = 'application/json'

		tracks = []
		if filter != None:
			try:
				tracks.extend(cherrypy.request.db.query(Track).filter(Track.id == filter).order_by(Track.title_sort, Track.title).all())
			except:
				pass

			# only attempt a name match if the id match failed - this prevents 12 from returning D12
			if len(tracks) == 0:
				try:
					tracks.extend(cherrypy.request.db.query(Track).filter(Track.title.like('%' + filter + '%')).order_by(Track.title_sort, Track.title).all())
				except:
					pass
		else:
			tracks.extend(cherrypy.request.db.query(Track).order_by(Track.title_sort, Track.title).all())

		track_list = []
		for a in tracks:
			track_list.append(a.as_dict())
		return json.dumps(track_list)