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
		#regex = re.compile('genre|artist|album|track')
		cherrypy.response.headers['Content-Type'] = 'application/json'

		#the first item in the url is the object that is being queried
		#the remainder are key value pairs of the things to query and their desired ids
		#split them into a list of dictionary pairs prior to processing
		query = []
		for index in range(1, len(params) - 1, 2):
			query.append(dict([(params[index],params[index + 1])]))

		#figure out data type the user is requesting
		if params[0] == 'albums':
			return json.dumps(self.queryAlbums(query))
		if params[0] == 'artists':
			return json.dumps(self.queryArtists(query))



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


	def queryAlbums(self, params):
		"""Assembles an album query by appending query parameters as filters.
		The result is a query that satisfies all of the parameters that were
		passed on the url string.
		Returns the results of the query sorted by title_sort property
		"""
		q = cherrypy.request.db.query(Album)

		for d in params:
			key = d.keys()[0]
			value = d[key]

			if key == 'id':
				q = q.filter(Album.id == value)
			elif key == 'title':
				q = q.filter(Album.title.like('%' + value + '%'))
			elif key == 'title_sort':
				q = q.filter(Album.title_sort.like('%' + value + '%'))
			elif key == 'artist_id':
				q = q.filter(Album.artist_id == value)
			elif key == 'asin':
				q = q.filter(Album.asin.like('%' + value + '%'))
			elif key == 'barcode':
				q = q.filter(Album.barcode.like('%' + value + '%'))
			elif key == 'compilation':
				q = q.filter(Album.compilation == value)
			elif key == 'media_type':
				q = q.filter(Album.media_type.like('%' + value + '%'))
			elif key == 'musicbrainz_albumid':
				q = q.filter(Album.musicbrainz_albumid.like('%' + value + '%'))
			elif key == 'musicbrainz_albumstatus':
				q = q.filter(Album.musicbrainz_albumstatus.like('%' + value + '%'))
			elif key == 'musicbrainz_albumtype':
				q = q.filter(Album.musicbrainz_albumtype.like('%' + value + '%'))
			elif key == 'organization':
				q = q.filter(Album.organization.like('%' + value + '%'))
			elif key == 'releasecountry':
				q = q.filter(Album.releasecountry.like('%' + value + '%'))

		album_list = []
	 	for a in q.order_by(Album.title_sort).all():
	 		album_list.append(a.as_dict())
		return album_list


	def queryArtists(self, params):
		q = cherrypy.request.db.query(Artist)

		for d in params:
			key = d.keys()[0]
			value = d[key]

			if key == 'id':
				q = q.filter(Artist.id == value)
			elif key == 'name':
				q = q.filter(Artist.name.like('%' + value + '%'))
			elif key == 'name_sort':
				q = q.filter(Artist.name_sort.like('%' + value + '%'))
			elif key == 'musicbrainz_artistid':
				q = q.filter(Artist.musicbrainz_artistid.like('%' + value + '%'))

		artist_list = []
	 	for a in q.order_by(Artist.name_sort).all():
	 		artist_list.append(a.as_dict())
		return artist_list


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