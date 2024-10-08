"""Source compilation into binaries

This module uses Cython to compile Python v3 source codes into C binaries
The C binaries compiled by Cython can be imported as any other Python module
"""
from Cython.Build import cythonize
from setuptools import Extension, setup
from glob import iglob
from os import environ

APP_NAME = environ.get('APP_NAME', default='App Name')
APP_VERSION = environ.get('APP_VERSION', default='1.0.0')
PROJECT_NAME = environ.get('PROJECT_NAME', default='project-name')
PROJECT_DESCRIPTION = environ.get(
    'PROJECT_DESCRIPTION',
    default='{} v{}'.format(APP_NAME, APP_VERSION),
)
MAINTAINER = environ.get('MAINTAINER', default='Fernando R Abreu')

true_strings = ('true', 'yes', 'y', '1')
SINGLE_BINARY = str(environ.get('SINGLE_BINARY', default=False)).lower() in true_strings
VERBOSE = str(environ.get('VERBOSE', default=False)).lower() in true_strings


print(f'{PROJECT_NAME} Compile :: Prepare source files')

modules = list(set([f for f in iglob('src/**/*.py', recursive=True) if '/__' not in f]))
extensions = []

if SINGLE_BINARY:  # todo: this works, but atm the App does not start
    extension = Extension('app', modules)
    extensions.append(extension)

else:
    for filepath in modules:
        module = '.'.join(filepath.split('/')[1:]).replace('.py', '')
        extension = Extension(module, [filepath])
        extensions.append(extension)


print(f'{PROJECT_NAME} Compile :: Start compilation')

res = setup(
    name=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    long_description=PROJECT_DESCRIPTION,
    version=APP_VERSION,
    packages=['app'],
    package_dir={'app': 'src/app'},
    # install_requires=['prettyconf'],
    ext_modules=cythonize(extensions, compiler_directives={'language_level': '3'}),
    # entry_points={
    #     'console_scripts': [
    #         'run = run:start',
    #         'app = app:run',
    #         'start = app:start',
    #     ]
    # },
    maintainer=MAINTAINER,
    verbose=VERBOSE,
    password='xpto',  # todo, by ChatGPT: ensure this is secure if actually needed
)

BUILD_DIR = res.get_cmdline_options().get("build_ext", {}).get("build-lib")
print(
    '{} Compile :: Compilation ends. Binar{} placed in {}/.'.format(
        PROJECT_NAME, 'ies' if not SINGLE_BINARY else 'y', BUILD_DIR,
    ),
)
