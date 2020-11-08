import unittest
from test import test_selectors

from gi.repository import GLib

from asyncio_glib import glib_selector


class GLibSelectorTests(test_selectors.BaseSelectorTestCase):

    def SELECTOR(self):
        return glib_selector.GLibSelector(GLib.MainContext.default())

    def test_select_interrupt_exc(self):
        raise unittest.SkipTest("TODO")

    def test_select_interrupt_noraise(self):
        raise unittest.SkipTest("TODO")
