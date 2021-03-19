from typing import Callable
import unittest
import asyncio
from asyncio_glib import glib_events
from ddt import ddt, data
import threading
import time
from gi.repository import GLib

# The default policy with a poor_mans_gmainloop attached serves as the
# reference of the desired behavior.
POLICIES = [
  None,  # default policy
  glib_events.GLibEventLoopPolicy()
]


@ddt
class asyncio_glib_test(unittest.TestCase):
    def setUp(self):
        self._tasks = []

    def tearDown(self):
        # Clean up tasks nicely
        for task in self._tasks:
            task.cancel()
        # Give some time to cancel
        self._loop.call_later(0.1, self._loop.stop)
        self._loop.run_forever()
        # And actually close
        self._loop.close()

    def _setup_loop(self, policy):
        asyncio.set_event_loop_policy(policy)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._exception = None

        def exception_handler(loop, context):
            exception = context.get('exception')
            if exception:
                self._exception = exception
                loop.stop()

        self._loop.set_exception_handler(exception_handler)

        def guard():
            raise TimeoutError("Got stuck")
        task = self._loop.call_later(3, guard)
        self._tasks.append(task)

    def _attach_poor_mans_gmainloop(self):
        # Very straight forward and inefficient 'integration' of a gmainloop.
        # However due to its simplicity, it supports full compatibility and
        # thus surves as a good ref for the tests.
        async def gmainloop_task():
            while True:
                ctx = GLib.MainContext.default()
                while ctx.pending():
                    ctx.iteration(False)
                await asyncio.sleep(0.001)
        task = self._loop.create_task(gmainloop_task())
        self._tasks.append(task)

    def run_against_ref(func: Callable):
        # Decorator providing some extra setup
        # which is not possible in the 'setUp' function.
        @data(*POLICIES)
        def inner(self, policy):
            self._setup_loop(policy)
            # Make the default loop behave
            # fully GLib compatible (AKA our ref).
            if policy is None:
                self._attach_poor_mans_gmainloop()
            func(self)
            # Make sure the test fails when any of the async
            # task throws an exception.
            if self._exception is not None:
                raise self._exception
        return inner

    @run_against_ref
    def test_glib_cb_call_soon(self):
        glib_timeout_called = False

        def glib_cb():
            nonlocal glib_timeout_called
            self._loop.call_soon(self._loop.stop)
            glib_timeout_called = True

        GLib.timeout_add(10, glib_cb)

        self._loop.run_forever()
        self.assertTrue(glib_timeout_called)

    @run_against_ref
    def test_glib_cb_set_future_result(self):
        glib_timeout_called = False
        ran_on_future_stop = False
        future = self._loop.create_future()

        def glib_cb():
            nonlocal future, glib_timeout_called
            future.set_result(True)
            glib_timeout_called = True

        GLib.timeout_add(10, glib_cb)

        async def future_stop_task():
            nonlocal ran_on_future_stop, future
            await future
            self._loop.stop()
            ran_on_future_stop = True

        self._loop.create_task(future_stop_task())
        self._loop.run_forever()
        self.assertTrue(glib_timeout_called)
        self.assertTrue(ran_on_future_stop)

    @run_against_ref
    def test_await_subprocess(self):
        ran_task = False

        async def subprocess_task():
            nonlocal ran_task
            proc = await asyncio.create_subprocess_shell(
                "echo test"
            )
            rc = await proc.wait()
            self.assertEqual(rc, 0)
            ran_task = True
            asyncio.get_event_loop().stop()

        self._loop.create_task(subprocess_task())
        self._loop.run_forever()
        self.assertTrue(ran_task)

    @run_against_ref
    def test_await_subprocess_with_stdout(self):
        ran_task = False

        async def subprocess_task():
            nonlocal ran_task
            proc = await asyncio.create_subprocess_shell(
                "echo test", stdout=asyncio.subprocess.PIPE
            )
            out, _ = await proc.communicate()
            self.assertEqual(out.decode(), "test\n")
            ran_task = True
            asyncio.get_event_loop().stop()

        self._loop.create_task(subprocess_task())
        self._loop.run_forever()
        self.assertTrue(ran_task)

    @run_against_ref
    def test_await_future(self):
        ran_set_future_result = False
        ran_on_future_stop = False
        future = asyncio.get_event_loop().create_future()

        async def set_future_result_task():
            nonlocal ran_set_future_result, future
            await asyncio.sleep(0.1)
            future.set_result(True)
            ran_set_future_result = True

        async def future_stop_task():
            nonlocal ran_on_future_stop, future
            await future
            asyncio.get_event_loop().stop()
            ran_on_future_stop = True

        self._loop.create_task(set_future_result_task())
        self._loop.create_task(future_stop_task())
        self._loop.run_forever()
        self.assertTrue(ran_set_future_result)
        self.assertTrue(ran_on_future_stop)

    @run_against_ref
    def test_await_future_thread(self):
        ran_set_future_result = False
        ran_on_future_stop = False
        future = self._loop.create_future()

        def set_future_result_task():
            nonlocal ran_set_future_result, future
            time.sleep(0.1)

            def set_future():
                future.set_result(True)
            self._loop.call_soon_threadsafe(set_future)
            ran_set_future_result = True

        thread = threading.Thread(target=set_future_result_task)
        thread.start()

        async def future_stop_task():
            nonlocal ran_on_future_stop, future
            await future
            self._loop.stop()
            ran_on_future_stop = True

        self._loop.create_task(future_stop_task())
        self._loop.run_forever()
        thread.join()
        self.assertTrue(ran_set_future_result)
        self.assertTrue(ran_on_future_stop)
