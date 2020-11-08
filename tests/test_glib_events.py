import unittest

from test.test_asyncio.test_events import UnixEventLoopTestsMixin
try:
    from test.test_asyncio import utils as test_utils
except ImportError:
    from asyncio import test_utils

from asyncio_glib import glib_events
import gi
from gi.repository import GLib

class GLibEventLoopTests(UnixEventLoopTestsMixin, test_utils.TestCase):

    def create_event_loop(self):
        return glib_events.GLibEventLoop(main_context=GLib.MainContext.default())


class GLibEventLoopPolicyTests(unittest.TestCase):

    def create_policy(self):
        return glib_events.GLibEventLoopPolicy()

    def test_get_event_loop(self):
        policy = self.create_policy()
        loop = policy.get_event_loop()
        self.assertIsInstance(loop, glib_events.GLibEventLoop)
        self.assertIs(loop, policy.get_event_loop())
        loop.close()

    def test_new_event_loop(self):
        policy = self.create_policy()
        loop = policy.get_event_loop()
        self.assertIsInstance(loop, glib_events.GLibEventLoop)
        loop.close()

    def test_set_event_loop(self):
        raise unittest.SkipTest("Not compatible with GLib")
