r'''
cx_freeze setup program for making stand-alone Python executables.
    Parameter example:

    program_name = '4pc'             # Name of the main .py program
    root_dir = 'src\fourplayerchess'                # Name of the source directory
    added_datafiles = ['sensors.cfg']    # Files to copy into the app folder
    version = 1.1.0.0                    # Program version

'''
import os
import errno
import cx_Freeze
import sys
import warnings
# import numpy as np
from shutil import move, rmtree, copytree, copyfile
from site import getsitepackages
from glob import glob
# from utilities.gui import images


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def _numpy_dll_path():
    import numpy as np
    root = os.path.dirname(np.__file__)
    for _i in range(3):
        root = os.path.dirname(root)

    library_path = os.path.join(root, 'Library', 'bin')
    return library_path


def numpy_data_files():
    """ Return numpy external data files.

    Numpy in anaconda is built by default with MKL support.
    Since cx_Freeze can not find them at runtime, they must be included manually.

    This is still (21 Dec 2017) an open issue according to
    https:/github.com/anthony-tuininga/cx_Freeze/issues/199

    Currently only 4 of the mkl_*.dll are needed and included

    They are typically needed if you use matplotlib to plot numpy arrays.

    """
    library_path = _numpy_dll_path()
    # 'mkl_avx2.dll', 'mkl_rt.dll'  # Add if needed
    mkl_files = ['mkl_core.dll', 'mkl_def.dll', 'mkl_intel_thread.dll', 'libiomp5md.dll']
    data_files = [(library_path, file_) for file_ in mkl_files]
    return data_files


def _get_include_files(root, module):
    root1 = os.path.abspath(root)
    base_path = os.path.join(root1, module)
    skip_count = len(root1) + len(os.path.sep)
    include_files = []
    for folder, _subfolders, files in os.walk(base_path):
        for file_ in files:
            source = os.path.join(folder, file_)
            target = source[skip_count:]
            include_files.append(("{}".format(source),
                                  "{}".format(target)))
    return include_files


def _ignore(src, names):
    ignored_names = []
    for name in names:
        if name.split('.')[-1] == 'pyc':
            ignored_names.append(name)
    return ignored_names


def _copy_file_or_folder(root_dir, target_dir, f):
    src = os.path.join(root_dir, f)
    dst = os.path.join(target_dir, f)
    if os.path.isdir(src):
        copytree(src, dst, ignore=_ignore)
    else:
        mkdir_p(os.path.dirname(dst))
        copyfile(src, dst)


def _get_python_dlls(target_dir):
    """ Return list with complete path to required python dlls

    These dlls are needed to start python.
    """
    version = sys.version_info[:2]
    python_dlls = [os.path.join(target_dir, "python%s%s.dll" % version)]
    python_dlls.extend(glob(os.path.join(target_dir, 'msvc*.dll')))
    python_dlls.extend(glob(os.path.join(target_dir, 'mkl*.dll')))
    return python_dlls


def _move(f, folder):
    try:
        return move(f, folder)
    except Exception as error:
        warnings.warn(str(error))
        return False


def _move_dlls_to_lib(target_dir, lib_dir):
    """
    Move all pyd- and dll-files to the lib-folder,
    except python27.dll, mkl_rt.dll and the msvc*.dll which are needed to start Python.
    """
    if not os.path.exists(lib_dir):
        os.mkdir(lib_dir)

    python_dlls = _get_python_dlls(target_dir)
    status = []
    for extension in ['*.pyd', '*.dll']:
        for f in glob(os.path.join(target_dir, extension)):
            if f not in python_dlls:
                status.append(_move(f, lib_dir))

    for f in _get_python_dlls(lib_dir):
        status.append(_move(f, target_dir))

    return status


def _find_icon(icon_name):
    """Return full path to the icon
    """
    if not icon_name.endswith('.ico'):
        icon_name += '.ico'
    # images_root = os.path.dirname(images.__file__)
    icon_path = icon_name
    icon = icon_path if os.path.exists(icon_path) else None
    if icon_name and icon is None:
        print("Unable to find icon: {}".format(icon_name))
    return icon


def make_standalone_executable(source_name, root_dir,
                               target_name='',
                               icon_name='',
                               includes=(),
                               excludes=(),
                               packages=(),
                               folders=(),
                               internal_datafiles=(),
                               external_datafiles=(),
                               zip_include_packages=(),
                               zip_exclude_packages='*',
                               version="1.0.0.0",
                               base="Win32GUI",
                               optimize=2):
    """
    Parameters
    ----------
    source_name:
        Name of the main .py program
    root_dir
        Name of the source directory
    target_name:
        Name of standalone
    icon_name:
        Name of icon.
    includes:
        Comma separated list of names of modules to include
    excludes:
        Comma separated list of names of modules to exclude
    packages:
        Comma separated list of packages to include, which includes all
        submodules in the package
    folders:
        Comma separated list of subfolders of the python/lib/sitepackages folder
        to be copied to the target directory
    internal_datafiles:
        Comma separated list of file or subfolders to be copied to the target
        directory
    external_datafiles:
        Comma separated list of tuples of (rootfolder, file/subfolders) to be
        copied to the target directory
    zip_include_packages:
        List of packages which should be included in zip-file.
        Use "*" to include all files.
    zip_exclude_packages:
        List of packages which should be included from the zip-file and placed
        in the file system instead; Default is "*" which means all files.
    version:
        version number
    base:
        The name of the base executable to use which, if given as a
        relative path, will be joined with the bases subdirectory of the
        cx_Freeze installation; the default value is "Win32GUI"
        "Win32GUI", "Console"
    optimize:
        Optimization level, one of 0 (disabled), 1 or 2

    Notes
    -----
    If startuptimes for your frozen script get unreasonably long, you may
    download Process Monitor v3.32 or newer to investigate it and pinpoint
    the process responsible.

    If your application does not close. You may set base=None to uncover the console.

    """

    target_name = target_name if target_name else source_name
    icon_name = icon_name if icon_name else target_name

    print('Started building {}!'.format(target_name))

    # This program will be run with 'build' as argument unless otherwise stated
    if len(sys.argv) <= 1:
        sys.argv.append("build")

    standalone_dir = 'standalone'
    target_dir = os.path.join(standalone_dir, target_name)
    script = os.path.join(root_dir, source_name + '.py')

    # Remove old program folder
    rmtree(target_dir, ignore_errors=True)

    if not os.path.exists(standalone_dir):
        os.mkdir(standalone_dir)
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    # Redirect standard output to file
    log_file = os.path.join(target_dir, 'build.log')
    stdout = sys.stdout
    sys.stdout = open(log_file, 'w')

    # Add the data files manually:
    for f in internal_datafiles:
        _copy_file_or_folder(root_dir, target_dir, f)

    for source, f in external_datafiles:
        _copy_file_or_folder(source, target_dir, f)

    # The ConsoleSetLibPathModified.py script is a copy of the
    # ConsoleSetLibPath.py which resides in the
    # 'site-packages\cx_Freeze\initscripts\' folder.
    # It has been modified to include the expression
    # "sys.path.append(r'lib')" etc.
    # This will make the executable find library files in the 'lib' folder.
    init_script = os.path.join(os.path.dirname(__file__), "__ConsoleSetLibPathModified.py")
    include_files = []
    site_packages_dir = getsitepackages()[-1]
    for walk_path in folders:
        include_files.extend(_get_include_files(site_packages_dir, walk_path))

    # Build options:
    #
    # build_exe: Directory for built executables and dependent files,
    #            defaults to build/
    # optimize: Optimization level, one of 0 (disabled), 1 or 2
    # excludes: Comma separated list of names of modules to exclude
    # includes: Comma separated list of names of modules to include
    # packages: Comma separated list of packages to include, which includes all
    #           submodules in the package
    # namespace_packages: Comma separated list of packages to be treated as
    #                     namespace packages (path is extended using pkgutil)
    # replace_paths: Modify filenames attached to code objects, which appear in
    #                tracebacks. Pass a comma separated list of paths in the
    #                form <search>=<replace>.
    #                The value * in the search portion will match the directory
    #                containing the entire package, leaving just the relative
    #                path to the module.
    # path: Comma separated list of paths to search; the default value is
    #       sys.path
    # compressed: Create a compressed zip file (Not available. Why?)
    # constants: Comma separated list of constant values to include in the
    #            constants module called BUILD_CONSTANTS in form <name>=<value>
    # include_files: List containing files to be copied to the target directory
    #                It is expected that this list will contain strings or
    #                2-tuples for the source and destination; the source can be
    #                a file or a directory (in which case the tree is copied
    #                except for .svn and CVS directories); the target must not
    #                be an absolute path
    # include_msvcr: Include the Microsoft Visual C runtime DLLs and
    #                (if necessary) the manifest file required to run the
    #                executable without needing the redistributable package
    #                installed
    # zip_includes: List containing files to be included in the zip file
    #               directory; it is expected that this list will contain
    #               strings or 2-tuples for the source and destination.
    # bin_includes: List of names of files to include when determining
    #               dependencies of binary files that would normally be
    #               excluded; note that version numbers that normally follow
    #               the shared object extension are stripped prior to
    #               performing the comparison
    # bin_excludes: List of names of files to exclude when determining
    #               dependencies of binary files that would normally be
    #               included; note that version numbers that normally follow
    #               the shared object extension are stripped prior to
    #               performing the comparison
    # bin_path_includes: List of paths from which to include files when
    #                    determining dependencies of binary files
    # bin_path_excludes: List of paths from which to exclude files when
    #                    determining dependencies of binary files
    # zip_include_packages': List of packages which should be included in zip-file.
    #                        Use "*" to include all files.
    # zip_exclude_packages': List of packages which should be included from the zip-file and
    #                        placed  in the file system instead;
    #                        Default is "*" which means all files.
    # silent: Suppress all output except warnings

    buildOptions = {
        'build_exe': target_dir,
        'optimize': optimize,
        'excludes': excludes,
        'includes': includes,
        'packages': packages,
        'namespace_packages': [],
        'replace_paths': [],
        'path': sys.path,
        # 'compressed': True,
        # 'copy_dependent_files': True,
        # 'create_shared_zip': True,
        # 'append_script_to_exe': True,
        # 'include_in_shared_zip': True,
        'zip_include_packages': zip_include_packages,
        'zip_exclude_packages': zip_exclude_packages,
        'constants': [],
        'include_files': include_files,
        'include_msvcr': True,
        'zip_includes': [],
        'bin_includes': [],
        'bin_excludes': [],
        'bin_path_includes': [],
        'bin_path_excludes': [],
        'silent': False,
    }

    # The options above are defaults for all executables.
    # Options below are for each specific executable.

    # init_script: The name of the script to use during initialization which,
    #              if given as a relative path, will be joined with the
    #              initscripts subdirectory of the cx_Freeze installation;
    #              the default value is "Console"
    # icon: Include the icon in the frozen executables on the Windows platform
    #       and alongside the frozen executable on other platforms
    # base: The name of the base executable to use which, if given as a
    #       relative path, will be joined with the bases subdirectory of the
    #       cx_Freeze installation; the default value is "Console"

    executables = [
        cx_Freeze.Executable(script=script,
                             initScript=init_script,
                             base=base,
                             targetName=target_name + '.exe',
                             icon=_find_icon(icon_name),
                             # shortcutName=None,
                             shortcutDir=None,
                             # copyright=None,
                             # trademarks=None
                             )]
    print('Freeeezing ....')
    cx_Freeze.setup(version=version,
                    executables=executables,
                    options=dict(build_exe=buildOptions))
    print('Finished freeeezing ....')

    # lib_dir = os.path.join(target_dir, 'lib')
    # _move_dlls_to_lib(target_dir, lib_dir)

    # Restore stdout and notify user.
    sys.stdout = stdout
    print('\nFinished building %s! See "%s" for details.' % (target_name, log_file))
