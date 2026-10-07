# Check report validation and summary generation.

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from summarize_benchmarks import VARIANTS, summarize


class TestSummaries(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        for variant, enable_mul in VARIANTS.items():
            report = {
                "schema_version": 1,
                "variant": variant,
                "enable_mul": enable_mul,
                "seed": 42,
                "clock_period_ns": 10,
                "measurement": "markers",
                "cases": [{"case_id": "case", "a": [[1]], "b": [[2]], "expected": [[2]], "cycles": 200 if variant == "sw" else 100}],
            }
            (self.directory / f"{variant}.json").write_text(json.dumps(report))

    def change(self, mutate):
        path = self.directory / "sw.json"
        report = json.loads(path.read_text())
        mutate(report)
        path.write_text(json.dumps(report))

    def test_reports_and_ratios(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result = summarize(self.directory)
        self.assertEqual(result["cases"][0]["shift_add_over_accel"], 2)
        self.assertEqual(result["cases"][0]["mul_over_accel_mul"], 1)
        for name in ["summary.json", "summary.csv", "summary.md"]:
            self.assertTrue((self.directory / name).is_file())

    def test_reject_mismatched_inputs(self):
        self.change(lambda report: report["cases"][0].update(a=[[3]]))
        with self.assertRaises(ValueError):
            summarize(self.directory)

    def test_reject_wrong_cpu(self):
        self.change(lambda report: report.update(enable_mul=1))
        with self.assertRaises(ValueError):
            summarize(self.directory)

    def test_reject_invalid_cycles(self):
        self.change(lambda report: report["cases"][0].update(cycles=0))
        with self.assertRaises(ValueError):
            summarize(self.directory)

    def test_reject_missing_report(self):
        (self.directory / "mul.json").unlink()
        with self.assertRaises(FileNotFoundError):
            summarize(self.directory)
