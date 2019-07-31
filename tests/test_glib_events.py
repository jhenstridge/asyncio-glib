import unittest

from test.test_asyncio.test_events import UnixEventLoopTestsMixin
try:
    from test.test_asyncio import utils as test_utils
except ImportError:
    from asyncio import test_utils

from asyncio_glib import glib_events


class GLibEventLoopTests(UnixEventLoopTestsMixin, test_utils.TestCase):

    def create_event_loop(self):
        return glib_events.GLibEventLoop()

    def test_read_pipe(self):
        raise unittest.SkipTest("TODO")


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
        policy = self.create_policy()
        loop = policy.new_event_loop()
        policy.set_event_loop(loop)
        self.assertIs(loop, policy.get_event_loop())
        loop.close()
