class EasygoingDictionary(dict):
	"""A dictionary that returns None if you try to access a non-existent key.
	"""
	def __getitem__(self, key):
		if not key in self:
			return None
		return super(EasygoingDictionary, self).__getitem__(key)
