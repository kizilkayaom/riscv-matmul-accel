# Check valid and malformed benchmark write sequences.

import unittest

from benchmark_monitor import BenchmarkMonitor


class TestBenchmarkMonitor(unittest.TestCase):
    def make_monitor(self):
        return BenchmarkMonitor([-1, 2, 3, 4], "unit")

    def finish(self, monitor):
        for i, value in enumerate([0xFFFFFFFF, 2, 3, 4]):
            monitor.accept_write(i + 1, 0x700 + 4 * i, value, 15)
        monitor.accept_write(5, 0x7F4, 1, 15)

    def test_valid_interval_starts_at_zero(self):
        monitor = self.make_monitor()
        monitor.accept_write(0, 0x7F0, 1, 15)
        self.finish(monitor)
        self.assertEqual(monitor.elapsed_cycles, 5)

    def test_invalid_markers(self):
        for address in [0x7F0, 0x7F4]:
            for data, strobes in [(0, 15), (1, 1)]:
                with self.subTest(address=address, data=data, strobes=strobes):
                    with self.assertRaises(AssertionError):
                        self.make_monitor().accept_write(0, address, data, strobes)

    def test_end_before_start(self):
        with self.assertRaises(AssertionError):
            self.make_monitor().accept_write(0, 0x7F4, 1, 15)

    def test_missing_results(self):
        monitor = self.make_monitor()
        monitor.accept_write(0, 0x7F0, 1, 15)
        with self.assertRaises(AssertionError):
            monitor.accept_write(5, 0x7F4, 1, 15)

    def test_invalid_results(self):
        for address, data, strobes in [(0x700, 0, 15), (0x700, 0xFFFFFFFF, 1), (0x701, 0, 15)]:
            monitor = self.make_monitor()
            monitor.accept_write(0, 0x7F0, 1, 15)
            with self.subTest(address=address, data=data, strobes=strobes):
                with self.assertRaises(AssertionError):
                    monitor.accept_write(1, address, data, strobes)

    def test_results_outside_interval(self):
        monitor = self.make_monitor()
        with self.assertRaises(AssertionError):
            monitor.accept_write(0, 0x700, 0xFFFFFFFF, 15)
        monitor.accept_write(0, 0x7F0, 1, 15)
        self.finish(monitor)
        with self.assertRaises(AssertionError):
            monitor.accept_write(6, 0x700, 0xFFFFFFFF, 15)

    def test_duplicates(self):
        monitor = self.make_monitor()
        monitor.accept_write(0, 0x7F0, 1, 15)
        with self.assertRaises(AssertionError):
            monitor.accept_write(1, 0x7F0, 1, 15)
        monitor.accept_write(1, 0x700, 0xFFFFFFFF, 15)
        with self.assertRaises(AssertionError):
            monitor.accept_write(2, 0x700, 0xFFFFFFFF, 15)
        monitor = self.make_monitor()
        monitor.accept_write(0, 0x7F0, 1, 15)
        self.finish(monitor)
        with self.assertRaises(AssertionError):
            monitor.accept_write(6, 0x7F4, 1, 15)

    def test_timeout_and_firmware_error(self):
        monitor = self.make_monitor()
        with self.assertRaises(AssertionError):
            _ = monitor.elapsed_cycles
        with self.assertRaises(AssertionError):
            monitor.accept_write(1, 0x7F8, 2, 15)
