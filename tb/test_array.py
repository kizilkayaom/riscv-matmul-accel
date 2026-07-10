import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

def get_result(dut, r, c, N=2):
    idx = (r * N + c) * 32
    val = (int(dut.out.value) >> idx) & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val

@cocotb.test()
async def test_array(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Reset
    dut.reset.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    # Cycle 0
    dut.enable.value = 1
    dut.a_in.value = (0 & 0xFF) << 8 | (64 & 0xFF)
    dut.b_in.value = (0 & 0xFF) << 8 | (64 & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    # Cycle 1
    dut.a_in.value = (127 & 0xFF) << 8 | ((-128) & 0xFF)
    dut.b_in.value = ((-64) & 0xFF) << 8 | (127 & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    # Cycle 2
    dut.a_in.value = (32 & 0xFF) << 8 | (0 & 0xFF)
    dut.b_in.value = (32 & 0xFF) << 8 | (0 & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    # Drain — zero inputs
    dut.a_in.value = 0
    dut.b_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert get_result(dut, 0, 0) == -12160
    assert get_result(dut, 0, 1) == -8192
    assert get_result(dut, 1, 0) == 12192
    assert get_result(dut, 1, 1) == -7104