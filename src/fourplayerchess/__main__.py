#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of the Four-Player Chess project, a four-player chess GUI.
#
# Copyright (C) 2018, GammaDeltaII
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/

import os
import sys
# from utilities.global_settings.initialize_logger import logger
# from utilities.global_settings import standalone_logging  # @UnusedImport
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRect
from fourplayerchess.gui.main import MainWindow
from fourplayerchess import ROOT


def get_window(app):
    window = MainWindow()
    screen = QRect(app.desktop().availableGeometry())
    x = screen.left() + (screen.width() - window.width()) / 2
    y = screen.top() + (screen.height() - window.height()) / 2
    window.move(x, y)
    return window


def main():
    """Creates application and main window and sets application icon."""
    #logger.info('Finished imports, starting fourplayerchess.')
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(ROOT, 'resources', 'img', 'icon.svg')))
    window = get_window(app)
    window.show()
    try:
        app.exec_()
    except Exception as error:
        print(error)
    #logger.info('Ended fourplayerchess.')


if __name__ == '__main__':
    sys.exit(main())
