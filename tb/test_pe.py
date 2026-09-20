import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge

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
    dut.a_in.value = 5
    dut.b_in.value = 7
    await RisingEdge(dut.clk)
    expected = 5 * 7
    await Timer(1, unit="ns")
    assert dut.out.value == expected, f"Expected: {expected}, got {dut.out.value}"

    assert dut.a_pass.value == 5
    assert dut.b_pass.value == 7

    # Pair 2
    dut.a_in.value = 3
    dut.b_in.value = 4
    await RisingEdge(dut.clk)
    expected += 3 * 4
    await Timer(1, unit="ns")
    assert dut.out.value == expected, f"Expected: {expected}, got {dut.out.value}"

    assert dut.a_pass.value == 3
    assert dut.b_pass.value == 4

    # Reset before Pair 3
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 3 - Neg x Pos
    dut.a_in.value = -64
    dut.b_in.value = 32
    await RisingEdge(dut.clk)
    expected = -64 * 32
    await Timer(1, unit="ns")
    assert dut.out.value.to_signed() == expected, f"Expected: {expected}, got {dut.out.value}"

    assert dut.a_pass.value.to_signed() == -64
    assert dut.b_pass.value.to_signed() == 32

    # Reset before Pair 4
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 4 - Neg x Neg
    dut.a_in.value = -128
    dut.b_in.value = -128
    await RisingEdge(dut.clk)
    expected = -128 * -128
    await Timer(1, unit="ns")
    assert dut.out.value == expected, f"Expected: {expected}, got {dut.out.value}"

    # Reset before Pair 5
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 5 - Accumulator Saturation Test 1
    dut.out.value = 2147483647
    dut.a_in.value = 1
    dut.b_in.value = 1
    dut.enable.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.out.value.to_signed() == 2147483647

    # Reset before Pair 6
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 6 - Accumulator Saturation Test 2
    dut.out.value = -2147483648
    dut.a_in.value = -1
    dut.b_in.value = 1
    dut.enable.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.out.value.to_signed() == -2147483648

    # Reset before Pair 7
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 7 - Accumulator Saturation Test 3
    dut.out.value = 2147483647
    dut.a_in.value = -1
    dut.b_in.value = 1
    dut.enable.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.out.value.to_signed() == 2147483646

    # Reset before Pair 8
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0

    # Pair 8 - Accumulator Saturation Test 4
    dut.out.value = -2147483648
    dut.a_in.value = 1
    dut.b_in.value = 1
    dut.enable.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.out.value.to_signed() == -2147483647