"""Source compilation into binaries

This module uses Cython to compile Python v3 source codes into C binaries
The C binaries compiled by Cython can be imported as any other Python module
"""
from Cython.Distutils import build_ext
from distutils.extension import Extension
from distutils.core import setup
from glob import iglob
from os import environ

APP_NAME = environ.get("APP_NAME", "App Name")
APP_VERSION = environ.get("APP_VERSION", "1.0.0")
PROJECT_NAME = environ.get("PROJECT_NAME", "project-name")
PROJECT_DESCRIPTION = environ.get("PROJECT_DESCRIPTION", default="{} v{}".format(APP_NAME, APP_VERSION))

print(f"{PROJECT_NAME} Compile :: Prepare source files")

ext_modules = []
for filepath in iglob("src/**/*.py", recursive=True):
    if "__.py" in filepath:
        continue

    module = ".".join(filepath.split("/")[1:]).replace(".py", "")

    extension = Extension(module, [filepath])
    extension.cython_directives = {"language_level": "3"}
    ext_modules.append(extension)

print(f"{PROJECT_NAME} Compile :: Start binaries creation")

setup(
    name=PROJECT_NAME,
    description=APP_NAME,
    long_description=PROJECT_DESCRIPTION,
    version=APP_VERSION,
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
    install_requires=["prettyconf"],
    password="xpto",
)

print(f"{PROJECT_NAME} Compile :: Compilation ends. Binaries to be placed in build/app/")
