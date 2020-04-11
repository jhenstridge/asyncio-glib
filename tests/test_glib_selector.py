import unittest
from test import test_selectors

from gi.repository import GLib

from asyncio_glib import glib_selector


class GLibSelectorTests(test_selectors.BaseSelectorTestCase):

    def SELECTOR(self):
        main_context = GLib.MainContext.default()
        main_loop = GLib.MainLoop.new(main_context, False)
        return glib_selector.GLibSelector(main_context, main_loop)

    def test_select_interrupt_exc(self):
        raise unittest.SkipTest("TODO")
