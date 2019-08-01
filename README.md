# GLib event loop integration for asyncio

This module provides a Python 3 [asyncio][1] event loop implementation
that makes use of the [GLib event loop][2].  This allows for mixing of
asyncio and some GLib based code within the same thread.

Enabling this event loop can be achieved with the following code:

    import asyncio
    import asyncio_glib
    asyncio.set_event_loop_policy(asyncio_glib.GLibEventLoopPolicy())

At this point, `asyncio.get_event_loop()` will return a `GLibEventLoop`.

## Implementation strategy

To ease maintenance, I have tried to reuse as much of the standard
library asyncio code as possible.  To this end, I created a GLib
implementation of the [`selectors.BaseSelector`][3] API.  Combine this
with the existing `asyncio.SelectorEventLoop` class, and we have our
event loop implementation.

To test that the event loop is functional, I have reused parts of the
standard library test suite to run against the new selector and event
loop.

At present the selector sublcasses the private
`selectors._BaseSelectorImpl` class, which is a potential source of
future compatibility problems.  If that happens, taking a local copy
of that code is an option.

## Comparison with Gbulb

[Gbulb][4] is another implementation of the asyncio event loop on top
of GLib.  The main differences are:

 * Gbulb dispatches asyncio callbacks directly from the GLib main
   loop.  In contrast, asyncio-glib iterates the GLib main loop until
   an asyncio event is ready and then has asyncio event loop dispatch
   the event.

 * Gbulb has some Windows compatibility code, while asyncio-glib has
   had no testing on that platform.

 * asyncio-glib is an essentially unmodified `SelectorEventLoop`, so
   should automatically gain any features from new Python releases.

The asyncio-glib code base is also about one tenth of the size of Gbulb.

[1]: https://docs.python.org/3/library/asyncio.html
[2]: https://developer.gnome.org/glib/stable/glib-The-Main-Event-Loop.html
[3]: https://docs.python.org/3/library/selectors.html
[4]: https://github.com/nhoad/gbulb
