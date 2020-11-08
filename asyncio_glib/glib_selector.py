import selectors

from gi.repository import GLib


__all__ = (
    'GLibSelector',
)

class _SelectorSource(GLib.Source):
    """A GLib source that gathers selector """

    def __init__(self, selector):
        super().__init__()
        self._fd_to_tag = {}
        self._fd_to_events = {}
        self._selector = selector

    def prepare(self):
        timeout = self._selector._loop._get_timeout_ms()

        # NOTE: Always return False as we query the FDs in only in check
        return False, timeout

    def check(self):
        has_events = False
        timeout = self._selector._loop._get_timeout_ms()
        if timeout == 0:
            has_events = True

        for (fd, tag) in self._fd_to_tag.items():
            condition = self.query_unix_fd(tag)
            events = self._fd_to_events.setdefault(fd, 0)
            if condition & (GLib.IOCondition.IN | GLib.IOCondition.HUP):
                events |= selectors.EVENT_READ
                has_events = True
            if condition & GLib.IOCondition.OUT:
                events |= selectors.EVENT_WRITE
                has_events = True
            self._fd_to_events[fd] = events

        return has_events

    def dispatch(self, callback, args):
        # Now, wag the dog by its tail
        self._selector._loop._run_once()
        return GLib.SOURCE_CONTINUE

    def register(self, fd, events):
        assert fd not in self._fd_to_tag

        condition = GLib.IOCondition(0)
        if events & selectors.EVENT_READ:
            condition |= GLib.IOCondition.IN | GLib.IOCondition.HUP
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

    def __init__(self, context, loop):
        super().__init__()
        self._context = context
        self._loop = loop
        self._source = _SelectorSource(self)
        self._source.attach(self._context)

    def close(self):
        self._source.clear()
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
        # Dummy select that just returns immediately with what we already know.
        ready = []
        for key in self.get_map().values():
            events = self._source.get_events(key.fd) & key.events
            if events != 0:
                ready.append((key, events))
        self._source.clear()

        return ready
