"""
Script for making stand-alone Python executable.
"""

from cx_freeze_helper import make_standalone_executable  #, numpy_data_files)  # @UnusedImport

from fourplayerchess.make_config import (includes, excludes, packages, folders,
                                         zip_exclude_packages, zip_include_packages)

# Test standalone
# FourPlayerChess.exe --test  --nodialog -s --verbose --full-trace --timeout=1200

####################################
# Program and package info.
program_name = '__main__'    # Name of the main .py program
target_name = '4PlayerChess'
root_dir = r'src/fourplayerchess'           # Name of the source directory
icon_name = r'src/fourplayerchess/resources/img/icon.ico'
internal_datafiles = ['standalone_logging.conf'
                      #'README.md',
                      #'server.cfg',
                      #'matplotlibrc',  # make sure backend is "Agg"
                      #'tests'
                      ]  # Copied into the app folder
external_datafiles = []
# external_datafiles.extend(numpy_data_files())
version = '1.0.0.0'                         # Program version
base = "Win32GUI"                           # GUI application
#####################################


if __name__ == '__main__':
    make_standalone_executable(program_name,
                               root_dir,
                               target_name=target_name,
                               icon_name=icon_name,
                               includes=includes,
                               excludes=excludes,
                               packages=packages,
                               folders=folders,
                               internal_datafiles=internal_datafiles,
                               external_datafiles=external_datafiles,
                               zip_exclude_packages=zip_exclude_packages,
                               zip_include_packages=zip_include_packages,
                               version=version,
                               base=base)
