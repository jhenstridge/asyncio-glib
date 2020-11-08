import sys
import asyncio
from asyncio import events
import threading

from gi.repository import GLib

from . import glib_selector

# The override for GLib.MainLoop.run installs a signal wakeup fd,
# which interferes with asyncio signal handlers.  Try to get the
# direct version.
try:
    g_main_loop_run = super(GLib.MainLoop, GLib.MainLoop).run
except AttributeError:
    g_main_loop_run = GLib.MainLoop.run

__all__ = (
    'GLibEventLoop',
    'GLibEventLoopPolicy',
)


class GLibEventLoop(asyncio.SelectorEventLoop):
    """An asyncio event loop that runs the GLib context using a main loop"""

    # This is based on the selector event loop, but never actually runs select()
    # in the strict sense.
    # We use the selector to register all FDs with the main context using our
    # own GSource. For python timeouts/idle equivalent, we directly query them
    # from the context by providing the _get_timeout_ms function that the
    # GSource uses. This in turn access _ready and _scheduled to calculate
    # the timeout and whether python can dispatch anything non-FD based yet.
    #
    # To simplify matters, we call the normal _run_once method of the base
    # class which will call select(). As we know that we are ready at the time
    # that select() will return immediately with the FD information we have
    # gathered already.
    #
    # With that, we just need to override and slightly modify the run_forever
    # method so that it calls g_main_loop_run instead of looping _run_once.

    def __init__(self, main_context):
        # A mainloop in case we want to run our context
        assert main_context is not None
        self._context = main_context
        self._main_loop = GLib.MainLoop.new(self._context, False)

        selector = glib_selector.GLibSelector(self._context, self)
        super().__init__(selector)

        # This is used by run_once to not busy loop if the timeout is floor'ed to zero
        self._clock_resolution = 1e-3

    def run_forever(self):
        self._check_closed()
        self._check_running()
        self._set_coroutine_origin_tracking(self._debug)
        self._thread_id = threading.get_ident()

        old_agen_hooks = sys.get_asyncgen_hooks()
        sys.set_asyncgen_hooks(firstiter=self._asyncgen_firstiter_hook,
                               finalizer=self._asyncgen_finalizer_hook)
        try:
            events._set_running_loop(self)
            g_main_loop_run(self._main_loop)
        finally:
            self._thread_id = None
            events._set_running_loop(None)
            self._set_coroutine_origin_tracking(False)
            sys.set_asyncgen_hooks(*old_agen_hooks)

    def time(self):
        return GLib.get_monotonic_time() / 1000000

    def _get_timeout_ms(self):
        if self._ready:
            return 0

        if self._scheduled:
            timeout = (self._scheduled[0]._when - self.time()) * 1000
            return timeout if timeout >= 0 else 0

        return -1

    def is_running(self):
        # If we are currently the owner, then the context is running
        # (and we are being dispatched by it)
        if self._context.is_owner():
            return True

        # Otherwise, it might (but shouldn't) be running in a different thread
        # Try aquiring it, if that fails, another thread is owning it
        if not self._context.acquire():
            return True
        self._context.release()

        return False

    def stop(self):
        self._main_loop.quit()

class GLibEventLoopPolicy(events.AbstractEventLoopPolicy):
    """An asyncio event loop policy that runs the GLib main loop"""

    _loops = {}

    def get_event_loop(self):
        """Get the event loop for the current context.

        Returns an event loop object implementing the BaseEventLoop interface,
        or raises an exception in case no event loop has been set for the
        current context and the current policy does not specify to create one.

        It should never return None."""
        # Get the thread default main context
        ctx = GLib.MainContext.get_thread_default()
        # If there is none, and we are on the main thread, then use the default context
        if ctx is None and threading.current_thread() is threading.main_thread():
            ctx = GLib.MainContext.default()
        # Otherwise, if there is still none, create a new one for this thread and push it
        if ctx is None:
            ctx = GLib.MainContext.new()
            ctx.push_thread_default()

        # Note: We cannot attach it to ctx, as getting the default will always
        #       return a new python wrapper. But, we can use hash() as that returns
        #       the pointer to the C structure.
        if ctx in self._loops:
            loop = self._loops[ctx]
            # If the loop is already closed, then return a new one instead
            if not loop._closed:
                return loop

        self._loops[ctx] = GLibEventLoop(ctx)
        return self._loops[ctx]

    def set_event_loop(self, loop):
        """Set the event loop for the current context to loop."""
        raise NotImplementedError

    def new_event_loop(self):
        """Create and return a new event loop object according to this
        policy's rules. If there's need to set this loop as the event loop for
        the current context, set_event_loop must be called explicitly."""
        raise NotImplementedError

    # Child processes handling (Unix only).

    def get_child_watcher(self):
        "Get the watcher for child processes."
        raise NotImplementedError

    def set_child_watcher(self, watcher):
        """Set the watcher for child processes."""
        raise NotImplementedError

