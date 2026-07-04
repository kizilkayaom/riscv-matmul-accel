import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_pe(dut):
    
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Reset the clock
    dut.reset.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    # Pair 1
    dut.enable.value = 1
    dut.in1.value = 5
    dut.in2.value = 7
    await RisingEdge(dut.clk)
    expected = 5 * 7
    await Timer(1, unit="ns")
    assert dut.out.value == expected, f"Expected: {expected}, got {dut.out.value}"

    # Pair 2
    dut.in1.value = 3
    dut.in2.value = 4
    await RisingEdge(dut.clk)
    expected += 3 * 4
    await Timer(1, unit="ns")
    assert dut.out.value == expected, f"Expected: {expected}, got {dut.out.value}"

    # Reset before Pair 3
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 3 - Neg x Pos
    dut.in1.value = -64
    dut.in2.value = 32
    await RisingEdge(dut.clk)
    expected = -64 * 32
    await Timer(1, unit="ns")
    assert dut.out.value.to_signed() == expected, f"Expected: {expected}, got {dut.out.value}"

    # Reset before Pair 4
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 4 - Neg x Neg
    dut.in1.value = -128
    dut.in2.value = -128
    await RisingEdge(dut.clk)
    expected = -128 * -128
    await Timer(1, unit="ns")
    assert dut.out.value == expected, f"Expected: {expected}, got {dut.out.value}"