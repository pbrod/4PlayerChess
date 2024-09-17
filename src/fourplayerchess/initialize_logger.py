'''
Import to initialize a logger object to use for logging in standalone.
The file standalone_logging.conf must be present in the directory of the
standalone.
'''
from __future__ import absolute_import, division, print_function
import logging.config
logging.config.fileConfig(fname='standalone_logging.conf')
logger = logging.getLogger('load_standalone')
logger.info('Starting to load program')
