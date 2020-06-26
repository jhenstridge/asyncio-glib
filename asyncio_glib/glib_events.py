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

    def create_task(self, *args, **kwargs):
        result = super().create_task(*args, **kwargs)
        self._selector._main_loop.quit()
        return result

    def create_future(self):
        # Just taking the regular Future here and setting an add_done_callback
        # would not cut it: Those done callbacks are executed from the Python
        # main loop and not when the result is set, thus we'd be waiting for
        # the very event we want to cause.
        return GLibFuture(loop=self)

class GLibEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """An asyncio event loop policy that runs the GLib main loop"""

    def new_event_loop(self):
        if threading.current_thread() != threading.main_thread():
            raise RuntimeError("GLibEventLoopPolicy only allows the main "
                               "thread to create event loops")
        return GLibEventLoop()

class GLibFuture(asyncio.Future):
    __slots__ = []

    def set_result(self, *args, **kwargs):
        self.get_loop()._selector._main_loop.quit()
        return super().set_result(*args, **kwargs)

    def set_exception(self, *args, **kwargs):
        self.get_loop()._selector._main_loop.quit()
        return super().set_exception(*args, **kwargs)
