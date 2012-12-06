import logging


def initLogging(moduleName):
	# set up logging
	log = logging.getLogger(moduleName)
	log.setLevel(logging.DEBUG)

	# create console handler and set level to debug
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)

	fs = logging.FileHandler(u'logs/%s.log' % moduleName)
	fs.setLevel(logging.DEBUG)

	# create formatter
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	# add formatter to ch
	ch.setFormatter(formatter)
	fs.setFormatter(formatter)

	# add ch to logger
	log.addHandler(ch)
	log.addHandler(fs)

	return log
