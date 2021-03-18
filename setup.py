import os
import re
import subprocess

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion


with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError as err:
            raise RuntimeError(
                'CMake must be installed to build the following extensions: ' +
                ', '.join(e.name for e in self.extensions)
            ) from err

        cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
        if cmake_version < LooseVersion('3.11.0'):
            raise RuntimeError('CMake >= 3.11.0 is required')

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        build_type = os.environ.get('BUILD_TYPE', 'Release')
        build_args = ['--config', build_type]
        build_args += ['--', '-j2']

        # Pile all .so in one place and use $ORIGIN as RPATH
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir]
        cmake_args += ['-DPYBIND11_TEST=OFF']
        cmake_args += ['-DCMAKE_BUILD_WITH_INSTALL_RPATH=TRUE']
        cmake_args += ['-DCMAKE_INSTALL_RPATH={}'.format('$ORIGIN')]
        cmake_args += ['-DCMAKE_BUILD_TYPE=' + build_type]

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.', '--target', ext.name] + build_args, cwd=self.build_temp)


setup(
    name='griffig',
    version='0.0.1',
    description='t',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Lars Berscheid',
    author_email='lars.berscheid@kit.edu',
    url='https://github.com/pantor/griffig',
    packages=find_packages(),
    license='LGPL',
    ext_modules=[CMakeExtension('_griffig')],
    cmdclass=dict(build_ext=CMakeBuild),
    keywords=['robot', 'robotics', 'grasping', 'robot-learning'],
    classifiers=[
        'Development Status :: 2 - Pre-Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: C++',
    ],
    python_requires='>=3.6',
)