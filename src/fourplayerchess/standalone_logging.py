"""
Import to redirect stdout and stderr to logfiles.
Also sets up an excepthook to properly catch and log exceptions.

Needs to have a logger set up beforehand to work,
e.q. by importing initialize_logger
"""
from __future__ import absolute_import, division, print_function
import sys
import logging
import traceback
from fourplayerchess.win32_utils import ErrorDlg


class StdoutWrapper(object):
    logger = logging.getLogger('stdout')

    def write(self, s):
        self.logger.info(s)

    def flush(self):
        pass



class StderrWrapper(object):
    logger = logging.getLogger('stderr')

    def write(self, s):
        self.logger.error(s)

    def flush(self):
        pass


def standalone_excepthook(ex_cls, ex, tb):
    logger = logging.getLogger('stderr')
    msg1 = ''.join(traceback.format_tb(tb))
    msg2 = '{0}: {1}'.format(ex_cls, ex)
    msg = '\n' + '\n'.join((msg1, msg2))
    logger.critical(msg)
    explanation_to_user = '''
    Something unexpected happened.
    The attempted action may not have been completed.
    The following traceback has been written to the log.
    It may provide insight into the cause of the problem.

    Note that tracebacks and logs may reveal classified information.

    '''
    if '--nodialog' not in sys.argv:
        ErrorDlg(explanation_to_user + msg, 'Unhandled exception')


if hasattr(sys, 'frozen') or True:
    sys.stdout = StdoutWrapper()
    sys.stderr = StderrWrapper()
    # wx.App(redirect) overwrites the same fields.

    sys.excepthook = standalone_excepthook
    logger = logging.getLogger('load_standalone')
    logger.info('Output streams and sys.excepthook set to logging.')
