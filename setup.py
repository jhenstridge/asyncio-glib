#!/usr/bin/env python3

from setuptools import setup

setup(
    name="asyncio-glib",
    version="0.0",
    description="GLib event loop integration for asyncio",
    author_emial="James Henstridge <james@jamesh.id.au>",
    packages=[
        "asyncio_glib",
    ],
    license="LGPL-2+",
    install_requires=["PyGObject"],
    test_suite="tests",
)
