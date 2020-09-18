import os
# Semantic versioning: N.N.N-{alpha|beta|rc}.N
MAJOR = str(0)
MINOR = str(10)
PATCH = str(0)
PRE_RELEASE = False * ('-' + 'alpha' + str(1))  # alpha, beta or rc (= release candidate)
VERSION = MAJOR + '.' + MINOR + '.' + PATCH + PRE_RELEASE
__version__ = "0.10.0"

_tmp = os.path.dirname(__file__)
print(_tmp)
ROOT = os.path.abspath(_tmp)
print(ROOT)