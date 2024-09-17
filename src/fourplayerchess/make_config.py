"""
Configuration for making stand-alone Python executable.
"""
from __future__ import absolute_import
from pytest import freeze_includes

# These modules cannot be found by cx_freeze, and must be included
# manually. If SciPy continues to be a problem, consider swallowing the
# whole package by including 'scipy' in the 'packages' list below instead.
includes = [] + freeze_includes()  # 'filecmp'
# These are modules to exclude from the build. If something doesn't work,
# try commenting out lines to include the modules again.
excludes = [
            'bottleneck',
            'Crypto',
            'pyzmq',
            'cython',
            'Cython',
            'IPython',
             'lxml',
             'OpenGL_accelerate',
             'gtk',
             'PyQt4',
#             'PyQt5',
             'Tkinter',
             'vtk',
             'jinja2',
             'numpy',
             'scipy',
             'statsmodels',
             'numba',
             'matplotlib',
#            'statsmodels.__init__',  # Possible bug in cx_freeze
            ]
# These packages will be included fully as-is with folders and files intact:

packages = ['PyQt5', "PyQt5.QtCore","PyQt5.QtGui", "PyQt5.QtWidgets",
            'os',
            'pkg_resources._vendor',
            'packaging',

            ]
zip_include_packages = []
#  ['scipy', 'pyacoustic', 'mpl_toolkits', 'pypressure',
#  'matplotlib', 'pandas', 'orakel', 'wx'],
zip_exclude_packages = ['PyQt5']  #'numpy', 'geomag' 'pyface', 'traitsui']

# These folders will be included fully as-is with all files intact:
folders = [
#     'pyface/images',
#            'pyface/dock/images',
#            'pyface/ui/wx/images',
#            'pyface/ui/wx/grid/images',
#            'traitsui/wx/images',
#            'traitsui/image/library'
           ]
