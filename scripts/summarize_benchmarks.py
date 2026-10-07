# Validate benchmark reports and summarize cycle comparisons.

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median


VARIANTS = {"accel": 0, "sw": 0, "accel_mul": 1, "mul": 1, "c": 0}


def summarize(directory):
    reports = {}
    reference = None
    for variant, enable_mul in VARIANTS.items():
        report = json.loads((directory / f"{variant}.json").read_text())
        if report["schema_version"] != 1 or report["variant"] != variant or report["enable_mul"] != enable_mul:
            raise ValueError(f"Invalid report configuration: {variant}")
        cases = report["cases"]
        if not cases or len({case["case_id"] for case in cases}) != len(cases):
            raise ValueError(f"Missing or duplicate cases: {variant}")
        # Require identical cases and timing boundaries.
        signature = [(case["case_id"], case["a"], case["b"], case["expected"]) for case in cases]
        signature += [(report["seed"], report["clock_period_ns"], report["measurement"])]
        if reference is not None and signature != reference:
            raise ValueError(f"Inputs or measurement boundaries differ: {variant}")
        reference = signature
        if any(type(case["cycles"]) is not int or case["cycles"] <= 0 for case in cases):
            raise ValueError(f"Invalid cycle count: {variant}")
        reports[variant] = report

    rows = []
    for i, case in enumerate(reports["accel"]["cases"]):
        row = {"case_id": case["case_id"]}
        row.update({variant: report["cases"][i]["cycles"] for variant, report in reports.items()})
        # Compare matching CPU configurations.
        row["shift_add_over_accel"] = row["sw"] / row["accel"]
        row["mul_over_accel_mul"] = row["mul"] / row["accel_mul"]
        row["c_over_assembly_accel"] = row["c"] / row["accel"]
        rows.append(row)

    stats = {}
    for variant in VARIANTS:
        values = [row[variant] for row in rows]
        stats[variant] = {"min": min(values), "median": median(values), "mean": mean(values), "max": max(values)}
    summary = {"schema_version": 1, "case_count": len(rows), "statistics": stats, "cases": rows}
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (directory / "summary.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# Benchmark results", "", f"{len(rows)} identical input cases per implementation; cycles between accepted marker writes.", "", "| Variant | Min | Median | Mean | Max |", "|---|---:|---:|---:|---:|"]
    for variant, values in stats.items():
        lines.append(f"| {variant} | {values['min']} | {values['median']:g} | {values['mean']:.2f} | {values['max']} |")
    lines += ["", "`accel` and `sw` use the CPU without hardware multiplication. `accel_mul` and `mul` both enable PicoRV32's iterative multiplier. `c` uses the C accelerator driver with multiplication disabled.", "", "Ratios compare these specific implementations at the same simulated clock period, including end-marker overhead. They do not measure synthesis frequency, area, or power.", "", "| Case | Accel | Shift/add | Accel + MUL | MUL | C driver | Shift/add / accel | MUL / accel + MUL |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['case_id']} | {row['accel']} | {row['sw']} | {row['accel_mul']} | {row['mul']} | {row['c']} | {row['shift_add_over_accel']:.2f} | {row['mul_over_accel_mul']:.2f} |")
    (directory / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6 + len(VARIANTS)]))
    print(f"\nReports: {directory / 'summary.json'}, {directory / 'summary.csv'}, {directory / 'summary.md'}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.reset:
        args.directory.mkdir(parents=True, exist_ok=True)
        for name in [*(f"{variant}.json" for variant in VARIANTS), "summary.json", "summary.csv", "summary.md"]:
            (args.directory / name).unlink(missing_ok=True)
    else:
        summarize(args.directory)
