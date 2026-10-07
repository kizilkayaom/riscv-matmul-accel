# Run firmware on the CPU and verify RAM results.

import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from model.golden_model import model

@cocotb.test()
async def test_soc(dut):
    dut.reset.value = 1
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    for _ in range(5):
        await RisingEdge(dut.clk)
    
    await Timer(1, unit="ns")
    dut.reset.value = 0
    A = np.array([[64, -128], [127, 32]], dtype=np.int8)
    B = np.array([[64, -64], [127, 32]], dtype=np.int8)
    expected_first, _ = model(A, B)
    expected_second, _ = model(np.zeros_like(A), B)
    expected_writes = [
        (0x40000008, 0x207F8040),
        (0x4000000C, 0x207FC040),
        (0x40000000, 1),
        (0x100, int(expected_first[0, 0])),
        (0x104, int(expected_first[0, 1])),
        (0x108, int(expected_first[1, 0])),
        (0x10C, int(expected_first[1, 1])),
        (0x40000008, 0),
        (0x40000000, 1),
        (0x110, int(expected_second[0, 0])),
        (0x114, int(expected_second[0, 1])),
        (0x118, int(expected_second[1, 0])),
        (0x11C, int(expected_second[1, 1])),
    ]
    write_index = 0

    for _ in range(200):
        await RisingEdge(dut.clk)
        assert int(dut.trap.value) == 0
        if int(dut.mem_valid.value) == 1 and int(dut.mem_ready.value) == 1 and int(dut.mem_wstrb.value) != 0:
            expected_addr, expected_data = expected_writes[write_index]
            assert int(dut.mem_addr.value) == expected_addr
            assert int(dut.mem_wdata.value) == (expected_data & 0xFFFFFFFF)
            assert int(dut.mem_wstrb.value) == 0xF
            write_index += 1
            if write_index == len(expected_writes):
                break
    else:
        assert False, f"Expected {len(expected_writes)} writes within 200 cycles, observed {write_index}."

    await Timer(1, unit="ns")
    for address, expected in expected_writes:
        if 0 <= address < 0x1000:
            assert int(dut.memory_inst.ram_inst.memory[address // 4].value) == (expected & 0xFFFFFFFF)

    for _ in range(20):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.trap.value) == 0
