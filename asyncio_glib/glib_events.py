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

    def __init__(self, main_context=None, handle_sigint=False):
        if main_context is None:
            main_context = GLib.MainContext.default()
        selector = glib_selector.GLibSelector(main_context, handle_sigint)
        self.selector = selector
        super().__init__(selector)

    def call_at(self, *args, **kwargs):
        self._write_to_self()
        return super().call_at(*args, **kwargs)

    def call_later(self, *args, **kwargs):
        self._write_to_self()
        return super().call_later(*args, **kwargs)

    def call_soon(self, *args, **kwargs):
        self._write_to_self()
        return super().call_soon(*args, **kwargs)

    def _add_callback(self, *args, **kwargs):
        self._write_to_self()
        return super()._add_callback(*args, **kwargs)

    def _write_to_self(self):
        # the superclass one would probably do
        # but this uses glib's eventfd rather than fake IO
        self.selector.quit()


class GLibEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """An asyncio event loop policy that runs the GLib main loop"""

    def new_event_loop(self):
        if threading.current_thread() != threading.main_thread():
            raise RuntimeError("GLibEventLoopPolicy only allows the main "
                               "thread to create event loops")
        return GLibEventLoop()
