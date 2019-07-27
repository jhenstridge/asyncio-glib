from test.test_asyncio import utils as test_utils
from test.test_asyncio.test_events import UnixEventLoopTestsMixin

from asyncio_glib import glib_events


class GLibEventLoopTests(UnixEventLoopTestsMixin, test_utils.TestCase):

    def create_event_loop(self):
        return glib_events.GLibEventLoop()
