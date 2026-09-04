#
# This is a cross-platform shared library prep/build mechanism.
# Tested on:
# OSX, Ubuntu, Fedora, and Windows
#
import os
import glob
import platform
import re
import sys
import shutil
from subprocess import Popen, PIPE
from tar_download import download_and_extract
try:
    from setuptools._distutils.sysconfig import get_python_lib
except ImportError:
    from distutils.sysconfig import get_python_lib
from subprocess import getstatusoutput

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
HUNSPELL_VERSION = os.environ.get('HUNSPELL_VERSION') or '1.7.0'
HUNSPELL_MINOR = '.'.join(HUNSPELL_VERSION.split('.')[:2])  # e.g. '1.7'

def include_dirs():
    return [
        os.path.abspath(os.path.join(BASE_DIR, 'hunspell')),
        os.path.abspath(os.path.join(BASE_DIR, 'external', 'hunspell-' + HUNSPELL_VERSION, 'src')),
    ]

def run_proc_delay_print(*args):
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    for line in stdout.decode(encoding='utf-8').split('\n'):
        print(line)
    for line in stderr.decode(encoding='utf-8').split('\n'):
        print(line, file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError("Process '{}' returned with a non-zero exit code".format(args))

def build_hunspell_package(directory, force_build=False):
    if platform.system() == 'Windows':
        raise RuntimeError("Cannot build directly for windows OS. Please build manually by follow instructions at /libs/msvc/README")

    build_path = os.path.join(BASE_DIR, 'external', 'build')
    lib_path = os.path.join(build_path, 'lib')
    if not os.path.exists(build_path):
        os.makedirs(build_path)

    if platform.system() == 'Linux':
        # Use the static library so the wheel is self-contained and auditwheel-compatible.
        # The autotools build produces both .so and .a; we only need the .a here.
        static_lib_path = os.path.join(lib_path, 'libhunspell-{}.a'.format(HUNSPELL_MINOR))
        already_built = os.path.exists(static_lib_path)
    else:  # OSX
        hunspell_so_dir = os.path.join(BASE_DIR, 'hunspell')
        hunspell_library_name = 'libhunspell-{}.dylib'.format(HUNSPELL_MINOR)
        build_lib_path = os.path.join(lib_path, 'libhunspell-{}.dylib'.format(HUNSPELL_MINOR))
        hunspell_so_path = os.path.join(hunspell_so_dir, hunspell_library_name)
        already_built = os.path.exists(hunspell_so_path)

    olddir = os.getcwd()
    if force_build or not already_built:
        if os.path.exists(lib_path):
            shutil.rmtree(lib_path)
        try:
            os.chdir(directory)
            # autopoint (from gettext) rejects configure.ac that declares a newer version
            # than the installed gettext. Downgrade the declaration to 0.19 so older
            # build environments work. The infrastructure is unused anyway (--disable-nls).
            configure_ac = os.path.join(directory, 'configure.ac')
            with open(configure_ac) as f:
                content = f.read()
            patched = re.sub(r'AM_GNU_GETTEXT_VERSION\(\[?[^\)\]]+\]?\)', 'AM_GNU_GETTEXT_VERSION(0.19)', content)
            if patched != content:
                with open(configure_ac, 'w') as f:
                    f.write(patched)
            run_proc_delay_print('autoreconf', '-vfi')
            # Use the same CC/CXX as the Python extension wrapper (system GCC
            # in the cibuildwheel environment). This static library gets linked
            # directly into the final .so, so it must share the wrapper's ABI
            # baseline - a newer compiler (e.g. gcc-toolset-14, present in the
            # manylinux_2_28 image) produces libstdc++ symbols newer than the
            # manylinux_2_28 policy allows, breaking the wheel on older systems
            # even though the build itself succeeds.
            _cc = os.environ.get('CC', 'gcc')
            _cxx = os.environ.get('CXX', 'g++')
            run_proc_delay_print('./configure', '--prefix='+build_path, '--disable-nls',
                                 'CC=' + _cc, 'CXX=' + _cxx,
                                 'CFLAGS=-fPIC -O3', 'CXXFLAGS=-fPIC -O3')
            run_proc_delay_print('make')
            run_proc_delay_print('make', 'install')
        finally:
            os.chdir(olddir)

        print("Built Hunspell library files:")
        for filename in os.listdir(lib_path):
            if os.path.isfile(os.path.join(lib_path, filename)):
                print('\t' + filename)

        if platform.system() != 'Linux':
            os.makedirs(hunspell_so_dir, exist_ok=True)
            shutil.copyfile(build_lib_path, hunspell_so_path)
            print("Copied binary to '{}'".format(hunspell_so_path))

    if platform.system() == 'Linux':
        return static_lib_path, lib_path
    else:
        return 'hunspell-{}'.format(HUNSPELL_MINOR), hunspell_so_dir

def pkgconfig(**kw):
    kw['include_dirs'] = include_dirs()
    kw['library_dirs'] = []
    kw['libraries'] = []
    kw['extra_link_args'] = []
    kw['language'] = 'c++'
    if platform.system() == 'Darwin':
        # See https://stackoverflow.com/questions/9795793/shared-library-dependencies-with-distutils
        kw['extra_link_args'] = ['-Wl,-rpath,"@loader_path/']
    # If changing to a dynamic link dependency
    # if platform.system() == 'Windows':
    #     # See https://stackoverflow.com/questions/62662816/how-do-i-use-the-correct-dll-files-to-enable-3rd-party-c-libraries-in-a-cython-c
    #     for filename in os.listdir(os.path.join(BASE_DIR, 'libs', 'msvc')):
    #         shutil.copyfile(os.path.join(BASE_DIR, 'libs', 'msvc', filename), os.path.join(BASE_DIR, 'hunspell', filename))

    if not os.path.exists(os.path.join(BASE_DIR, 'external', 'hunspell-' + HUNSPELL_VERSION)):
        # Prepare for hunspell if it's missing
        download_and_extract(
            'https://github.com/hunspell/hunspell/archive/v{}.tar.gz'.format(HUNSPELL_VERSION),
            os.path.join(BASE_DIR, 'external'))
        kw['include_dirs'] = include_dirs()

    if platform.system() == 'Windows':
        # These should be hardcoded to both architectures
        kw['libraries'] = ['libhunspell-msvc14-x64', 'libhunspell-msvc14-x86']
        kw['library_dirs'] = [os.path.join(BASE_DIR, 'libs', 'msvc')]
        kw['extra_link_args'] = ['/NODEFAULTLIB:libucrt.lib ucrt.lib']
    else:
        force_build = os.environ.get('CYHUNSPELL_FORCE_BUILD', False)
        if force_build == '0' or force_build == 0:
            force_build = False
        lib_name, lib_path = build_hunspell_package(
            os.path.join(BASE_DIR, 'external', 'hunspell-' + HUNSPELL_VERSION), force_build)
        if platform.system() == 'Linux':
            # lib_name is the path to libhunspell-1.7.a; statically link it into the extension
            kw['extra_objects'] = [lib_name]
        else:
            kw['library_dirs'] = [lib_path]
            kw['libraries'] = [lib_name]

    return kw

def get_build_dir():
    build_base_long = [arg[12:].strip("= ") for arg in sys.argv if arg.startswith("--build-base")]
    build_base_short = [arg[2:].strip(" ") for arg in sys.argv if arg.startswith("-b")]
    build_base_arg = build_base_long or build_base_short
    if build_base_arg:
        return build_base_arg[0]
    else:
        return "."

def repair_darwin_link_dep_path():
    # Needed for darwin generated SO files to correctly look in the @loader_path for shared dependencies
    build_hunspell_lib_path = os.path.join(BASE_DIR, 'external', 'build', 'lib',
                                           'libhunspell-{}.dylib'.format(HUNSPELL_MINOR))
    for lib_path in (
            list(glob.glob(os.path.join(BASE_DIR, 'hunspell', '**', '*.so'), recursive=True)) +
            list(glob.glob(os.path.join(get_build_dir(), '**', '*.so'), recursive=True)
        )):
        print("Found *.so lib to modify: {}".format(lib_path))

        lib_name = os.path.basename(lib_path)
        print("Current lib '{}' id:".format(lib_name))
        run_proc_delay_print('otool', '-D', lib_path)
        print("Current lib '{}' paths:".format(lib_name))
        run_proc_delay_print('otool', '-L', lib_path)

        run_proc_delay_print('install_name_tool', '-id', '@loader_path/{}'.format(lib_name), lib_path)
        run_proc_delay_print('install_name_tool', '-change', build_hunspell_lib_path,
                             '@loader_path/libhunspell-{}.dylib'.format(HUNSPELL_MINOR), lib_path)

        print("Changed lib '{}' id:".format(lib_name))
        run_proc_delay_print('otool', '-D', lib_path)
        print("Changed lib '{}' paths:".format(lib_name))
        run_proc_delay_print('otool', '-L', lib_path)

    for lib_path in (
            list(glob.glob(os.path.join(BASE_DIR, 'hunspell', '**', '*.dylib'), recursive=True)) +
            list(glob.glob(os.path.join(get_build_dir(), '**', '*.dylib'), recursive=True))
        ):
        print("Found *.dylib dependency lib to modify: {}".format(lib_path))

        lib_name = os.path.basename(lib_path)
        print("Current lib '{}' id:".format(lib_name))
        run_proc_delay_print('otool', '-D', lib_path)
        print("Current lib '{}' paths:".format(lib_name))
        run_proc_delay_print('otool', '-L', lib_path)

        run_proc_delay_print('install_name_tool', '-id', '@loader_path/{}'.format(lib_name), lib_path)
        run_proc_delay_print('install_name_tool', '-change', build_hunspell_lib_path,
                             '@loader_path/libhunspell-{}.dylib'.format(HUNSPELL_MINOR), lib_path)

        print("Changed lib '{}' id:".format(lib_name))
        run_proc_delay_print('otool', '-D', lib_path)
        print("Changed lib '{}' paths:".format(lib_name))
        run_proc_delay_print('otool', '-L', lib_path)
