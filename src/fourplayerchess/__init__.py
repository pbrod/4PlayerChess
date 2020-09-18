import os
# Semantic versioning: N.N.N-{alpha|beta|rc}N
# alpha, beta or rc (= release candidate)


__version__ = "0.10.2"

VERSION = __version__
MAJOR, MINOR, _patch_and_prerelease = VERSION.split('.')
PATCH, _sep, PRE_RELEASE = _patch_and_prerelease.partition('-')

_tmp = os.path.dirname(__file__)
print(_tmp)
ROOT = os.path.abspath(_tmp)
print(ROOT)