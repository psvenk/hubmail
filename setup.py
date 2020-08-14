#!/usr/bin/env python3

from setuptools import setup, find_packages
try:
    from build_manpages.build_manpages \
        import build_manpages, get_build_py_cmd, get_install_cmd
    from setuptools.command.build_py import build_py
    from setuptools.command.install import install
    MANPAGES = True
except ModuleNotFoundError:
    MANPAGES = False

params = {
    "name": "hubmail",
    "version": "0.1",
    "author": "psvenk",
    "description": (
        "A tool to export GitHub issues and pull requests as email messages"
    ),
    "license": "LGPL-2.1-or-later",
    "long_description": open("README.md").read(),
    "packages": find_packages(),
    "package_data": {
        "": ["data/*"],
    },
    "entry_points": {
        "console_scripts": ["hubmail = hubmail.__main__:main"],
    },
    "python_requires": ">= 3.7"
}

if MANPAGES:
    params["cmdclass"] = {
        "build_manpages": build_manpages,
        "build_py": get_build_py_cmd(build_py),
        "install": get_install_cmd(install),
    }

setup(**params)
