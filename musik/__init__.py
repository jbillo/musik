import logging
import os


def initLogging(moduleName):
	# set up logging
	log_dir = os.path.join(os.path.dirname(__file__), "logs")  # default logging location

	if not os.path.isdir(log_dir):
		try:
			os.mkdir(log_dir)
		except IOError:
			print u"Could not create log directory {0}; this will likely cause problems".format(log_dir)

	log = logging.getLogger(moduleName)
	log.setLevel(logging.DEBUG)

	# create console handler and set level to debug
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)

	fs = logging.FileHandler(u'{0}/{1}.log'.format(log_dir, moduleName))
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
