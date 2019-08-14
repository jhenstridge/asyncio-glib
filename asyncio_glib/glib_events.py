import asyncio
import threading

from gi.repository import GLib

from . import glib_selector


__all__ = (
    'GLibEventLoop',
    'GLibEventLoopPolicy',
)


class GLibEventLoop(asyncio.SelectorEventLoop):
    """An asyncio event loop that runs the GLib main loop"""

    def __init__(self, main_context=None):
        if main_context is None:
            main_context = GLib.MainContext.default()
        selector = glib_selector.GLibSelector(main_context)
        super().__init__(selector)


class GLibEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """An asyncio event loop policy that runs the GLib main loop"""

    def new_event_loop(self):
        if threading.current_thread() != threading.main_thread():
            raise RuntimeError("GLibEventLoopPolicy only allows the main "
                               "thread to create event loops")
        return GLibEventLoop()
