"""GLib main loop integration for asyncio

By integrating with the GLib main loop, it is possible for asyncio
applications to make use of libraries built on top of the GLib main
loop.

This event loop implementation can be enabling its policy:

    >>> import asyncio
    >>> import asyncio_glib
    >>> asyncio.set_event_loop_policy(asyncio_glib.GLibEventLoopPolicy())

From this point on the asyncio API can be used as usual.
"""

from .glib_events import GLibEventLoop, GLibEventLoopPolicy


__all__ = (
    "GLibEventLoop",
    "GLibEventLoopPolicy",
)
