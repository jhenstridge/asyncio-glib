import asyncio

from gi.repository import GLib

from . import glib_selector


class GLibEventLoop(asyncio.SelectorEventLoop):
    def __init__(self, main_context=None):
        if main_context is None:
            main_context = GLib.MainContext.default()
        selector = glib_selector.GLibSelector(main_context)
        super().__init__(selector)
