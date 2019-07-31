#!/usr/bin/env python3

from setuptools import setup

setup(
    name="asyncio-glib",
    version="0.1",
    description="GLib event loop integration for asyncio",
    author="James Henstridge",
    author_email="james@jamesh.id.au",
    url="https://github.com/jhenstridge/asyncio-glib",
    packages=[
        "asyncio_glib",
    ],
    license="LGPL-2+",
    install_requires=["PyGObject"],
    test_suite="tests",
)
