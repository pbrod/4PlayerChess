#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup file for fourplayerchess.


Usage:
Run all tests:
  python setup.py test

  python setup.py doctest

Build documentation

  python setup.py docs

Install
  python setup.py install [, --prefix=$PREFIX]

Build

  python setup.py bdist_wininst

  python setup.py bdist_wheel --universal

  python setup.py sdist


  git pull origin
  git shortlog v0.6.0..HEAD -w80 --format="* %s" --reverse > log.txt
  # update CHANGELOG.md with info from log.txt

  python build_package.py 0.7.0
or
  update version number to 0.7.0 in src/fourplayerchess/__init__.py
  python setup.py doctest  # test docs
  python setup.py docs  # create documentation
  python setup.py sdist  # create source distribution
  python setup.py bdist_wheel # create wheel

  git commit
  git tag v0.7.0 master
  git push --tags

Notes
-----
Don't use package_data and/or data_files, use include_package_data=True and MANIFEST.in instead!
Don't hard-code the list of packages, use setuptools.find_packages() instead!


See also
--------
https://docs.pytest.org/en/latest/goodpractices.html
https://python-packaging.readthedocs.io/en/latest/
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/
https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure
https://ep2015.europython.eu/conference/talks/less-known-packaging-features-and-tricks
https://realpython.com/documenting-python-code/#public-and-open-source-projects

"""
import os
import re
import sys
from setuptools import setup, find_packages, Command
HERE = os.path.abspath(os.path.dirname(__file__))
PACKAGE_NAME = 'fourplayerchess'


def read(*parts, lines=False):
    with open(os.path.join(HERE, *parts), 'r') as fp:
        if lines:
            return fp.readlines()
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)  # @UndefinedVariable
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


class Doctest(Command):
    description = 'Run doctests with Sphinx'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from sphinx.application import Sphinx
        sph = Sphinx('./docs',  # source directory
                     './docs',  # directory containing conf.py
                     './docs/_build',  # output directory
                     './docs/_build/doctrees',  # doctree directory
                     'doctest')  # finally, specify the doctest builder
        sph.build()


class Latex(Command):
    description = 'Run latex with Sphinx'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from sphinx.application import Sphinx
        sph = Sphinx('./docs',  # source directory
                     './docs',  # directory containing conf.py
                     './docs/_build/latex',  # output directory
                     './docs/_build/doctrees',  # doctree directory
                     'latex')  # finally, specify the latex builder
        sph.build()


def setup_package():
    version = find_version('src', PACKAGE_NAME, "__init__.py")
    print("Version: {}".format(version))

    sphinx_requires = ['sphinx>=1.3.1']
    needs_sphinx = {'build_sphinx'}.intersection(sys.argv)
    sphinx = ['numpydoc', 'imgmath',
              'sphinx_rtd_theme>=0.1.7'] + sphinx_requires if needs_sphinx else []
    setup(
        name=PACKAGE_NAME,
        version=version,
        description='A Four-Player Chess Teams app variant to perform analysis',
        long_description=read('README.md'),
        author='GDII',
        url='https://github.com/GammaDeltaII/4PlayerChess',
        license='GPL',
        packages=find_packages('src'),  # include all packages under src
        package_dir={'': 'src'},   # tell distutils packages are under src
        cmdclass={'doctest': Doctest,
                  'latex': Latex},
        install_requires=read('requirements.txt', lines=True),
        include_package_data=True,  # include everything in source control + MANIFEST.in
        extras_require={'build_sphinx': sphinx_requires,},
        setup_requires=["pytest-runner"] + sphinx,
        tests_require=['pytest'],
        zip_safe=False,
        entry_points={"gui_scripts": ["4pc=fourplayerchess.__main__:main"]},
        python_requires='>=3.6'
    )


if __name__ == "__main__":
    setup_package()

