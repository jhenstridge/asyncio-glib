import selectors

from gi.repository import GLib


__all__ = (
    'GLibSelector',
)


# The override for GLib.MainLoop.run installs a signal wakeup fd,
# which interferes with asyncio signal handlers.  Try to get the
# direct version.
try:
    g_main_loop_run = super(GLib.MainLoop, GLib.MainLoop).run
except AttributeError:
    g_main_loop_run = GLib.MainLoop.run


class _SelectorSource(GLib.Source):
    """A GLib source that gathers selector """

    def __init__(self, main_loop):
        super().__init__()
        self._fd_to_tag = {}
        self._fd_to_events = {}
        self._main_loop = main_loop

    def prepare(self):
        return False, -1

    def check(self):
        return False

    def dispatch(self, callback, args):
        for (fd, tag) in self._fd_to_tag.items():
            condition = self.query_unix_fd(tag)
            events = self._fd_to_events.setdefault(fd, 0)
            if condition & GLib.IOCondition.IN:
                events |= selectors.EVENT_READ
            if condition & GLib.IOCondition.OUT:
                events |= selectors.EVENT_WRITE
            self._fd_to_events[fd] = events
        self._main_loop.quit()
        return GLib.SOURCE_CONTINUE

    def register(self, fd, events):
        assert fd not in self._fd_to_tag

        condition = GLib.IOCondition(0)
        if events & selectors.EVENT_READ:
            condition |= GLib.IOCondition.IN
        if events & selectors.EVENT_WRITE:
            condition |= GLib.IOCondition.OUT
        self._fd_to_tag[fd] = self.add_unix_fd(fd, condition)

    def unregister(self, fd):
        tag = self._fd_to_tag.pop(fd)
        self.remove_unix_fd(tag)

    def get_events(self, fd):
        return self._fd_to_events.get(fd, 0)

    def clear(self):
        self._fd_to_events.clear()


class GLibSelector(selectors._BaseSelectorImpl):

    def __init__(self, context):
        super().__init__()
        self._context = context
        self._main_loop = GLib.MainLoop.new(self._context, False)
        self._source = _SelectorSource(self._main_loop)
        self._source.attach(self._context)

    def close(self):
        self._source.destroy()
        super().close()

    def register(self, fileobj, events, data=None):
        key = super().register(fileobj, events, data)
        self._source.register(key.fd, events)
        return key

    def unregister(self, fileobj):
        key = super().unregister(fileobj)
        self._source.unregister(key.fd)
        return key

    def select(self, timeout=None):
        may_block = True
        self._source.set_ready_time(-1)
        if timeout is not None:
            if timeout > 0:
                self._source.set_ready_time(
                    GLib.get_monotonic_time() + int(timeout * 1000000))
            else:
                may_block = False

        self._source.clear()
        if may_block:
            g_main_loop_run(self._main_loop)
        else:
            self._context.iteration(False)

        ready = []
        for key in self.get_map().values():
            events = self._source.get_events(key.fd) & key.events
            if events != 0:
                ready.append((key, events))
        return ready
