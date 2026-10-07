# Compare firmware results and timing across shared matrix cases.

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from model.golden_model import model
from benchmark_monitor import BenchmarkMonitor

def observe_write(dut, monitor, cycle):
    if int(dut.mem_valid.value) and int(dut.mem_ready.value) and int(dut.mem_wstrb.value):
        address = int(dut.mem_addr.value)
        if 0x700 <= address < 0x710 or address in (0x7F0, 0x7F4, 0x7F8):
            monitor.accept_write(cycle, address, int(dut.mem_wdata.value), int(dut.mem_wstrb.value))


async def run_case(dut, A, B, case_id):
    expected, _ = model(A, B)
    packed_a = sum((int(value) & 0xFF) << (8 * i) for i, value in enumerate(A.flat))
    packed_b = sum((int(value) & 0xFF) << (8 * i) for i, value in enumerate(B.flat))

    dut.reset.value = 1

    for _ in range(5):
        await RisingEdge(dut.clk)
    
    await Timer(1, unit="ns")
    dut.memory_inst.ram_inst.memory[0x600 // 4].value = packed_a
    dut.memory_inst.ram_inst.memory[0x604 // 4].value = packed_b
    # Poison results to expose missing writes.
    for i, value in enumerate(expected.flat):
        dut.memory_inst.ram_inst.memory[0x700 // 4 + i].value = (int(value) ^ 0xFFFFFFFF) & 0xFFFFFFFF
    dut.reset.value = 0

    monitor = BenchmarkMonitor(expected.flat, case_id)

    for cycle in range(10000):
        await RisingEdge(dut.clk)
        assert int(dut.trap.value) == 0, f"{case_id}: CPU trapped at cycle {cycle}"
        # Sample accepted writes before register updates.
        observe_write(dut, monitor, cycle)
        if monitor.end_cycle is not None:
            break
    else:
        raise AssertionError(f"{case_id}: benchmark did not finish within 10000 cycles")

    elapsed_cycles = monitor.elapsed_cycles

    await Timer(1, unit="ns")
    for i, value in enumerate(expected.flat):
        assert int(dut.memory_inst.ram_inst.memory[0x700 // 4 + i].value) == (int(value) & 0xFFFFFFFF), f"{case_id}: RAM result {i} mismatch"
    
    # Catch writes after completion.
    for offset in range(1, 21):
        await RisingEdge(dut.clk)
        assert int(dut.trap.value) == 0, f"{case_id}: CPU trapped after completion"
        observe_write(dut, monitor, monitor.end_cycle + offset)
    await Timer(1, unit="ns")

    dut._log.info("%s: benchmark completed in %d cycles", case_id, elapsed_cycles)

    return {"case_id": case_id, "a": A.tolist(), "b": B.tolist(), "expected": expected.tolist(), "cycles": elapsed_cycles}


@cocotb.test()
async def test_benchmark(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    A = np.array([[64, -128], [127, 32]], dtype=np.int8)
    B = np.array([[64, -64], [127, 32]], dtype=np.int8)
    cases = [
        ("mixed signs", A, B),
        ("zero multipliers", A, np.zeros_like(B)),
        ("minimum multipliers", A, np.full_like(B, -128)),
        ("maximum multipliers", A, np.full_like(B, 127)),
    ]
    rng = np.random.default_rng(42)
    for i in range(20):
        cases.append((f"random {i}", rng.integers(-128, 128, size=(2, 2), dtype=np.int8), rng.integers(-128, 128, size=(2, 2), dtype=np.int8)))

    report_path = os.environ.get("BENCHMARK_REPORT")
    if report_path:
        Path(report_path).unlink(missing_ok=True)
    results = []
    for case_id, A, B in cases:
        results.append(await run_case(dut, A, B, case_id))

    if report_path:
        firmware = Path(os.environ["BENCHMARK_FIRMWARE"])
        report = {
            "schema_version": 1,
            "variant": os.environ["BENCHMARK_VARIANT"],
            "enable_mul": int(dut.ENABLE_MUL.value),
            "seed": 42,
            "clock_period_ns": 10,
            "measurement": "accepted start marker to accepted end marker; includes end marker overhead",
            "firmware_sha256": hashlib.sha256(firmware.read_bytes()).hexdigest(),
            "numpy_version": np.__version__,
            "python_version": sys.version.split()[0],
            "compiler_version": subprocess.check_output([os.environ.get("BENCHMARK_CC", "riscv64-elf-gcc"), "--version"], text=True).splitlines()[0],
            "cases": results,
        }
        destination = Path(report_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        # Publish only complete reports.
        temporary.replace(destination)
