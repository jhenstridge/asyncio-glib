#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="asyncio-glib",
    version="0.1",
    author="James Henstridge",
    author_email="james@jamesh.id.au",
    description="GLib event loop integration for asyncio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhenstridge/asyncio-glib",
    packages=[
        "asyncio_glib",
    ],
    license="LGPL-2.1+",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Operating System :: POSIX",
    ],
    install_requires=["PyGObject"],
    tests_require=["ddt"],
    test_suite="tests",
)
