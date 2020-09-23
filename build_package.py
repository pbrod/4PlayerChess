"""
Script to build the package.

The script removes the previous built binaries and generated documentation
before it generate the documentation and build the binaries and finally
check the built binaries.

It assumes that the library is installed in so called develop mode.

Created on 7. des. 2018

@author: pab
"""
import os
import re
import shutil
import subprocess

import click


ROOT = os.path.abspath(os.path.dirname(__file__))
PACKAGE_NAME = 'fourplayerchess'


def remove_previous_build():
    """Removes ./dist, ./build, ./docs/_build, and ./src/{}.egg-info directories.""".format(PACKAGE_NAME)
    egginfo_path = os.path.join('src', '{}.egg-info'.format(PACKAGE_NAME))
    docs_folder = os.path.join('docs', '_build')

    for dirname in ['dist', 'build', egginfo_path, docs_folder]:
        path = os.path.join(ROOT, dirname)
        if os.path.exists(path) and os.path.isdir(path):
            shutil.rmtree(path)


def set_package(version):
    """Set version of {} package""".format(PACKAGE_NAME)

    if version:
        filename = os.path.join(ROOT, "src", PACKAGE_NAME, "__init__.py")
        print("Version: {}".format(version))
        with open(filename, "r") as fid:
            text = fid.read()

        new_text = re.sub(r"__version__ = ['\"]([^'\"]*)['\"]",
                          '__version__ = "{}"'.format(version),
                          text, re.M)  # @UndefinedVariable

        with open(filename, "w") as fid:
            fid.write(new_text)


class ChangeDir:
    """Context manager for changing the current working directory"""
    def __init__(self, new_path):
        self.new_path = new_path

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def call_subprocess(cmd_opts):
    """Safe call to subprocess"""
    print("\n\n***********************************************")
    print("Running {}".format(' '.join(cmd_opts))
    try:
        subprocess.call(cmd_opts)
    except Exception as error:  # subprocess.CalledProcessError:
        print(str(error))
    print("***********************************************\n")



@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("version")
def build_main(version):
    """Build and update {} version, documentation and package.

    The script remove the previous built binaries and generated documentation
    before it generate the documentation and build the binaries.
    """.format(PACKAGE_NAME)
    remove_previous_build()
    set_package(version)

    for cmd in ['egg_info', 'sdist', 'bdist_wheel']: # 'doctest', 'docs', 'latexpdf',

        if cmd == 'latexpdf':
            with ChangeDir('./docs'):
                call_subprocess(["make.bat", cmd])
        else:
            call_subprocess(["python", "setup.py", cmd])


if __name__ == "__main__":
    import sys
    sys.argv = ['build_package', '0.10.2']
    build_main()

