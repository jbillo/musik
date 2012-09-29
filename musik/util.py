class EasygoingDictionary(dict):
	"""A dictionary that returns None if you try to access a non-existent key.
	"""
	def __getitem__(self, key):
		if not self.has_key(key):
			return None
		return super(Index,self).__getitem__(key)